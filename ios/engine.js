/**
 * Penname Mobile engine — a faithful client-side port of the Penname core.
 *
 * Mirrors penname/core:
 *   - detect/   → regex detectors + noise filter (Presidio/spaCy replaced by
 *                 a dependency-free detector set tuned for donor documents)
 *   - replace/  → span-safe application (end-to-start), longest-first reversal,
 *                 format-aware pen-name generation, round-trip verification
 *   - types/    → Mapping v1 JSON schema (identical entry shape to desktop)
 *   - mapping/  → AES-256-GCM .pnmap framing (WebCrypto; passphrase-derived
 *                 key via PBKDF2 — see README for the format difference)
 *
 * No network. No dependencies. Runs in any browser and in Node (for tests).
 */
"use strict";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

function mappingToDict(entries) {
  return {
    version: 1,
    entries: entries.map((e) => ({
      original: e.original,
      pen_name: e.pen_name,
      entity_type: e.entity_type,
      score: e.score,
    })),
  };
}

function mappingFromDict(data) {
  if (!data || data.version !== 1) {
    throw new Error("unsupported mapping version");
  }
  return (data.entries || []).map((e) => ({
    original: e.original,
    pen_name: e.pen_name,
    entity_type: e.entity_type,
    score: typeof e.score === "number" ? e.score : 1.0,
  }));
}

/* ------------------------------------------------------------------ */
/* Detection                                                          */
/* ------------------------------------------------------------------ */

const MONTHS = {
  january: 1, jan: 1, february: 2, feb: 2, march: 3, mar: 3, april: 4, apr: 4,
  may: 5, june: 6, jun: 6, july: 7, jul: 7, august: 8, aug: 8,
  september: 9, sep: 9, sept: 9, october: 10, oct: 10,
  november: 11, nov: 11, december: 12, dec: 12,
};

function luhnValid(digits) {
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = digits.charCodeAt(i) - 48;
    if (n < 0 || n > 9) return false;
    if (alt) { n *= 2; if (n > 9) n -= 9; }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}

function phoneValid(raw) {
  const digits = raw.replace(/\D/g, "");
  if (digits.length < 10 || digits.length > 15) return false;
  // Must be explicitly phone-shaped: country code, area brackets, or separators.
  if (!(/^\+/.test(raw) || /\(/.test(raw) || /[\s.-]/.test(raw))) return false;
  // Reject values that are just a run of identical digits (placeholders).
  if (/^(\d)\1+$/.test(digits)) return false;
  return true;
}

/* Words that appear capitalised in running text but are not names. */
const NOISE_WORDS = new Set((
  "the this that these those there here it its in on at as if so we our us you your " +
  "he she they them his her their my me am is are was were be been being do does did " +
  "have has had will would can could shall should may might must not no yes and but " +
  "or for with from into over under about after before when then now what which who " +
  "whom whose why how all any both each few more most other some such only own same " +
  "than too very just also please thank thanks hello hi dear kind best warm regards " +
  "sincerely yours faithfully truly again soon later welcome hope well good great new " +
  "next last first second third final annual spring summer autumn winter fall monday " +
  "tuesday wednesday thursday friday saturday sunday january february march april may " +
  "june july august september october november december donor donors donation " +
  "donations gift gifts amount total name names email phone address date fund funds " +
  "campaign appeal grant grants report board trustee trustees staff volunteer " +
  "volunteers member members meeting minutes notes summary update newsletter " +
  "application review committee director manager officer coordinator executive " +
  "chair chief executive ceo cfo finance finance team fundraising marketing " +
  "communications programme program project community supporters supporter patron " +
  "patrons friend friends letter letters page pages section chapter appendix " +
  "enclosure cc subject date received paid due balance invoice receipt " +
  "mr mrs ms miss mx dr prof rev sir dame lord lady st"
).split(/\s+/));

/* Headings / labels that must never be treated as donor data. */
const NOISE_PHRASES = new Set([
  "donor name", "donor names", "gift amount", "gift date", "total amount",
  "amount paid", "amount due", "constituent id", "donor id", "account name",
  "account number", "card number", "sort code", "bank details", "first name",
  "last name", "full name", "street address", "email address", "phone number",
  "mobile number", "thank you", "best regards", "kind regards", "warm regards",
  "yours sincerely", "yours faithfully", "dear friend", "dear supporter",
]);

/* Short upper-case tokens that look like names in ALL-CAPS text but are not. */
const CAPS_NOISE = new Set((
  "gdpr crm csv pdf usa uk us eu nhs ceo cfo coo cto id ref no tel fax aid hmrc " +
  "ltd plc llc inc cic vat pay pin dob ni faq tbc tbd asap fyi rsvp url www " +
  "confidential private draft urgent important attention note notes total"
).split(/\s+/));

function personLooksReal(value) {
  const v = value.trim();
  if (NOISE_PHRASES.has(v.toLowerCase())) return false;
  const words = v.split(/\s+/);
  for (const w of words) {
    const clean = w.toLowerCase().replace(/[^\p{Ll}]/gu, "");
    if (clean.length > 1 && (NOISE_WORDS.has(clean) || CAPS_NOISE.has(clean))) return false;
  }
  return true;
}

/* Name building blocks. Unicode-aware so accented names (José García) and
 * Irish/Scottish forms (O'Brien, McDonald) are caught. JavaScript's \b is
 * ASCII-only, and lookbehind needs iOS 16.4+ (we support iOS 15), so the
 * leading boundary is a consumed character and the name is capture group 1.
 * Separators are spaces/tabs only: a name never spans a line break, which
 * stops "Regards\nJane" from swallowing the name that follows. */
const NAME_PREFIX = "(?:Mc|Mac|O['’]|D['’])?";
const NAME_WORD = `${NAME_PREFIX}\\p{Lu}\\p{Ll}{2,}(?:[-'’]\\p{Lu}?\\p{Ll}{2,})*`;
const CAPS_WORD = `${NAME_PREFIX}\\p{Lu}{2,}(?:[-'’]\\p{Lu}{2,})?`;
const NAME_SEP = "[ \\t\\u00A0]+";
const NB = "(?:^|[^\\p{L}\\p{N}'’-])"; // name boundary, before
const NE = "(?![\\p{L}\\p{N}])";        // name boundary, after
const TITLES = "(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Rev|Sir|Dame|Lord|Lady)";
const nameRe = (body) => new RegExp(`${NB}(${body})${NE}`, "gu");

const DETECTORS = [
  { type: "EMAIL_ADDRESS", score: 0.95,
    re: /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g },
  { type: "URL", score: 0.85,
    re: /https?:\/\/[^\s<>"')\]]+/g },
  { type: "CREDIT_CARD", score: 0.9,
    re: /\b(?:\d[ -]?){13,19}\b/g,
    validate: (m) => luhnValid(m.replace(/[ -]/g, "")) },
  { type: "IBAN_CODE", score: 0.85,
    re: /\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,6}(?:[ ]?[A-Z0-9]{2})?\b/g },
  { type: "US_SSN", score: 0.9,
    re: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: "DONATION_AMOUNT", score: 0.85,
    re: /[$£€]\s?\d[\d,]*(?:\.\d{1,2})?(?:\s?(?:K|M|million|billion|bn)\b)?/g },
  { type: "DATE_TIME", score: 0.8,
    re: /\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b/gi },
  { type: "DATE_TIME", score: 0.8,
    re: /\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4}\b/gi },
  { type: "DATE_TIME", score: 0.6,
    re: /\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+\d{4}\b/g },
  { type: "DATE_TIME", score: 0.75,
    re: /\b\d{1,2}\/\d{1,2}\/\d{2,4}\b/g },
  { type: "DATE_TIME", score: 0.8,
    re: /\b\d{4}-\d{2}-\d{2}\b/g },
  { type: "PHONE_NUMBER", score: 0.7,
    re: /(?:\+\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?\d{3}[\s.-]?\d{3,4}(?:[\s.-]?\d{2,4})?/g,
    validate: phoneValid },
  { type: "PHONE_NUMBER", score: 0.7,
    re: /(?:\+\d{10,14}|\b0\d{9,10})\b/g,
    validate: (m) => !/^(\d)\1+$/.test(m.replace(/\D/g, "")) },
  { type: "UK_NINO", score: 0.85,
    re: /\b[A-Z]{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?[A-D]\b/g },
  { type: "SORT_CODE", score: 0.6,
    re: /\b\d{2}-\d{2}-\d{2}\b/g },
  { type: "BANK_ACCOUNT", score: 0.8,
    re: /\b(?:account|acct|a\/c)(?:\s+(?:no\.?|number|#))?\s*:?\s*(\d{8})\b/gi, group: 1 },
  { type: "LOCATION", score: 0.85,
    re: /\b[A-Z]{1,2}\d[A-Z\d]?[ \t]?\d[A-Z]{2}\b/g },
  { type: "LOCATION", score: 0.7,
    re: /\b\d{1,5}\s+[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Drive|Dr\.?|Boulevard|Blvd\.?|Way|Court|Ct\.?|Close|Place|Pl\.?|Terrace|Gardens|Grove|Hill|Park)\b/g },
  { type: "ORGANIZATION", score: 0.8,
    re: /\b[A-Z][A-Za-z&.'-]*(?:\s+(?:of|for|the|and|[A-Z][A-Za-z&.'-]+)){0,3}\s+(?:Foundation|Trust|Fund|Charity|Charities|Association|Society|CIC|Limited|Ltd\.?|LLC|Inc\.?|University|College|Hospital|Church|School|Academy|Council)\b/g },
  { type: "PERSON", score: 0.85,
    re: nameRe(`${TITLES}\\.?${NAME_SEP}${NAME_WORD}(?:${NAME_SEP}${NAME_WORD}){0,2}`), group: 1 },
  { type: "PERSON", score: 0.55,
    re: new RegExp(`\\bDear${NAME_SEP}(${NAME_WORD}(?:${NAME_SEP}${NAME_WORD}){0,2}),`, "gu"), group: 1 },
  { type: "PERSON", score: 0.5,
    re: nameRe(`\\p{Lu}\\.[ \\t]?${NAME_WORD}`), group: 1,
    validate: (m) => personLooksReal(m.slice(m.indexOf(".") + 1)) },
  { type: "PERSON", score: 0.4,
    re: nameRe(`${NAME_WORD}(?:${NAME_SEP}${NAME_WORD}){1,2}`), group: 1,
    validate: personLooksReal, rescue: NAME_WORD },
  { type: "PERSON", score: 0.35,
    re: nameRe(`${CAPS_WORD}(?:${NAME_SEP}${CAPS_WORD}){1,2}`), group: 1,
    validate: personLooksReal, rescue: CAPS_WORD },
  { type: "CONSTITUENT_ID", score: 0.7,
    re: /\b[A-Z]{1,3}-\d{3,8}\b/g },
  { type: "FUND_CODE", score: 0.65,
    re: /\b(?:Fund|Campaign|Appeal|Grant)\s?(?:Code|ID|No\.?|#)?\s?:?\s?([A-Z]{2,5}[-_]\d{2,6})\b/g,
    group: 1 },
];

/** Drop overlapping spans, preferring higher score then longer match. */
function selectSpans(spans) {
  const ranked = spans.slice().sort(
    (a, b) => (b.score - a.score) || (a.start - a.end) - (b.start - b.end)
  );
  const kept = [];
  for (const span of ranked) {
    if (kept.every((k) => span.end <= k.start || span.start >= k.end)) {
      kept.push(span);
    }
  }
  return kept.sort((a, b) => a.start - b.start);
}

/** A name candidate failed validation because noise words ride along
 *  ("From Harold Whitfield", "Jane Smith Thank"). Recover the real name:
 *  first the longest run of 2+ words inside the match that validates, then
 *  the trailing word extended by the name words that follow it. */
function rescueName(det, raw, idx, text) {
  const words = [];
  const wordRe = /\S+/g;
  let w;
  while ((w = wordRe.exec(raw)) !== null) words.push({ start: w.index, end: w.index + w[0].length });
  const make = (s, e) => ({ start: idx + s, end: idx + e, entity_type: det.type, score: det.score, text: text.slice(idx + s, idx + e) });
  for (let len = words.length - 1; len >= 2; len--) {
    for (let st = 0; st + len <= words.length; st++) {
      const sub = raw.slice(words[st].start, words[st + len - 1].end);
      if (det.validate(sub)) return make(words[st].start, words[st + len - 1].end);
    }
  }
  const last = words[words.length - 1];
  if (!det.validate(raw.slice(last.start, last.end))) return null;
  const after = text.slice(idx + raw.length);
  for (const n of [2, 1]) {
    const ext = after.match(new RegExp(`^(?:${NAME_SEP}${det.rescue}){${n}}${NE}`, "u"));
    if (ext && det.validate(raw.slice(last.start) + ext[0])) {
      return make(last.start, raw.length + ext[0].length);
    }
  }
  return null;
}

/** Once "Jane Smith" is found, a later bare "Smith" or "Jane" is the same
 *  person and must not leak. Flag each name part wherever it stands alone. */
function namePartSpans(text, spans) {
  const parts = new Set();
  for (const s of spans) {
    if (s.entity_type !== "PERSON") continue;
    const words = s.text.split(/[ \t ]+/);
    if (words.length < 2) continue;
    for (const word of words) {
      const clean = word.replace(/[.,'’]+$/u, "");
      if (clean.length >= 3 && personLooksReal(clean) && !/^\p{Lu}\.$/u.test(clean)) parts.add(clean);
    }
  }
  if (!parts.size) return [];
  // One pass over the words of the text (a regex per part is O(parts × text)
  // and freezes on large donor lists).
  const found = [];
  const tokenRe = /\p{L}[\p{L}'’-]*/gu;
  let m;
  while ((m = tokenRe.exec(text)) !== null) {
    const token = m[0].replace(/['’]s$/u, "");
    if (parts.has(token)) {
      found.push({ start: m.index, end: m.index + token.length, entity_type: "PERSON", score: 0.3, text: token });
    }
  }
  return found;
}

function detectSpans(text) {
  const spans = [];
  for (const det of DETECTORS) {
    det.re.lastIndex = 0;
    let m;
    while ((m = det.re.exec(text)) !== null) {
      if (m.index === det.re.lastIndex) det.re.lastIndex++; // zero-width safety
      const raw = m[det.group || 0];
      if (!raw || !raw.trim()) continue;
      const idx = det.group ? m.index + m[0].lastIndexOf(raw) : m.index;
      if (det.validate && !det.validate(raw)) {
        const rescued = det.rescue ? rescueName(det, raw, idx, text) : null;
        if (rescued) spans.push(rescued);
        continue;
      }
      spans.push({
        start: idx, end: idx + raw.length,
        entity_type: det.type, score: det.score, text: raw,
      });
    }
  }
  const kept = selectSpans(spans);
  return selectSpans(kept.concat(namePartSpans(text, kept)));
}

/* ------------------------------------------------------------------ */
/* Pen-name generation (format-aware, session-consistent)             */
/* ------------------------------------------------------------------ */

const FIRST_NAMES = ("Dorothy Eleanor Margaret Joan Barbara Alice Florence Grace Edith " +
  "Martha Clara Rose Helen Iris Vera Nora Beatrice Sylvia Agnes Frances " +
  "Harold Walter Arthur Frank Albert Ernest Herbert Ronald Leonard Peter " +
  "Gerald Raymond Clifford Maurice Stanley Bernard Dennis Geoffrey Brian").split(" ");

const LAST_NAMES = ("Hartley Whitfield Ashworth Pemberton Fairbanks Hollis Kirkbride " +
  "Marlowe Ellison Thackeray Winslow Carrington Fenwick Alderton Greywell " +
  "Prescott Larkin Danvers Ellsworth Hargrave Winspeare Blackwood Cavendish " +
  "Rutledge Fairholme Underhill Stanmore Collingwood Ashcombe Merriweather " +
  "Lockwood Ravensworth Thornbury Waverly Eastwood Hallowell").split(" ");

const CITIES = ("Ashford Bridgewater Claymont Doverhurst Eastvale Fairmont Glenbrook " +
  "Havenport Kingsley Larkspur Millbrook Northgate Oakhaven Pinehurst " +
  "Riverton Stonebridge Thornbury Westfield Wexley").split(" ");

const ORG_SUFFIXES = ["Foundation", "Trust", "Fund", "Charitable Trust", "Initiative"];

/* Composed surnames widen the pool from ~1.4k to ~13k distinct person
 * stand-ins, so large donor lists do not run out. */
const SURNAME_STEMS = ("Ash Brad Brook Carl Dun Elm Fair Glen Hart Holm Kings Lang Mar " +
  "Nor Oak Pem Rad Stan Thorn Wes Whit Win Ald Bel Crans Dal").split(" ");
const SURNAME_ENDS = "ley ton ford field wood worth well by ham combe dale more stead wick bury".split(" ");
const PERSON_SURNAMES = [...new Set(LAST_NAMES.concat(
  SURNAME_STEMS.flatMap((s) => SURNAME_ENDS.map((e) => s + e))
))];
const STREET_NAMES = [...new Set(PERSON_SURNAMES.concat(CITIES))];
const UK_POSTCODE = /^[A-Z]{1,2}\d[A-Z\d]?[ \t]?\d[A-Z]{2}$/;
const NAME_SPLIT = /[ \t ]+/;

function makeRng(seed) {
  if (seed === undefined) {
    // Cryptographic randomness by default.
    return function rng() {
      const buf = new Uint32Array(1);
      crypto.getRandomValues(buf);
      return buf[0] / 4294967296;
    };
  }
  // Deterministic LCG for tests.
  let s = seed >>> 0;
  return function rng() {
    s = (1664525 * s + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

class PenNameError extends Error {}

class PenNameGenerator {
  constructor(seed) {
    this.rng = makeRng(seed);
    this.cache = new Map();   // (type|value) -> pen name
    this.used = new Set();
    this.pinned = new Set();
    const sign = this.rng() < 0.5 ? -1 : 1;
    this.dateDelta = sign * Math.floor(30 + this.rng() * 371); // days
  }

  penNameFor(entityType, original, avoidText) {
    const key = entityType + "|" + original;
    const cached = this.cache.get(key);
    if (cached !== undefined) return cached;
    const accept = (candidate) => {
      if (!candidate || candidate === original || this.used.has(candidate) || avoidText.includes(candidate)) {
        return false;
      }
      this.cache.set(key, candidate);
      this.used.add(candidate);
      return true;
    };
    // A bare "Smith" after "Jane Smith" reuses the matching half of that
    // person's stand-in, so the safe copy still reads naturally.
    if (entityType === "PERSON" && original.split(NAME_SPLIT).length === 1) {
      const derived = this._nameHalf(original);
      if (derived && accept(derived)) return derived;
    }
    for (let i = 0; i < 50; i++) {
      const candidate = this._generate(entityType, original);
      if (accept(candidate)) return candidate;
    }
    // Last resort for very large lists: a middle initial multiplies the pool.
    if (entityType === "PERSON") {
      for (let i = 0; i < 50; i++) {
        const [first, last] = this._personName().split(" ");
        const initial = "ABCDEFGHJKLMNPRSTW"[this._int(0, 17)];
        const candidate = `${first} ${initial}. ${last}`;
        if (accept(candidate)) return candidate;
      }
    }
    throw new PenNameError("could not generate a pen name for a " + entityType + " value");
  }

  _nameHalf(part) {
    for (const [key, pen] of this.cache) {
      if (!key.startsWith("PERSON|")) continue;
      const words = key.slice(7).split(NAME_SPLIT);
      const penWords = pen.split(NAME_SPLIT);
      const at = words.indexOf(part);
      if (at < 0 || words.length < 2 || penWords.length < 2) continue;
      return at === 0 ? penWords[0] : penWords[penWords.length - 1];
    }
    return null;
  }

  forget(entityType, original) {
    const key = entityType + "|" + original;
    if (this.pinned.has(key)) return;
    const pen = this.cache.get(key);
    if (pen !== undefined) {
      this.cache.delete(key);
      this.used.delete(pen);
    }
  }

  pinPenName(entityType, original, penName) {
    const key = entityType + "|" + original;
    const previous = this.cache.get(key);
    if (previous !== undefined) this.used.delete(previous);
    this.cache.set(key, penName);
    this.used.add(penName);
    this.pinned.add(key);
  }

  /* --- generators ------------------------------------------------- */

  _pick(arr) { return arr[Math.floor(this.rng() * arr.length)]; }
  _int(lo, hi) { return lo + Math.floor(this.rng() * (hi - lo + 1)); }

  _digit() { return String(this._int(0, 9)); }

  _personName() { return this._pick(FIRST_NAMES) + " " + this._pick(PERSON_SURNAMES); }

  _location(original) {
    if (UK_POSTCODE.test(original)) return this._reshapeAlnum(original);
    // "12 High Street" → "87 Fenwick Street": keep the address shape (number,
    // street type) and draw the street name from a large pool.
    const m = original.match(/^(\d{1,5})(\s+)(.+?)(\s+)(\S+)$/);
    if (m) return this._int(1, 299) + m[2] + this._pick(STREET_NAMES) + m[4] + m[5];
    return this._pick(STREET_NAMES);
  }

  _reshapeDigits(original) {
    return original.replace(/\d/g, () => this._digit());
  }

  _reshapeAlnum(original) {
    return original.replace(/[A-Za-z0-9]/g, (ch) => {
      if (ch >= "0" && ch <= "9") return this._digit();
      const letter = "abcdefghijklmnopqrstuvwxyz"[this._int(0, 25)];
      return ch === ch.toUpperCase() ? letter.toUpperCase() : letter;
    });
  }

  _reshapeAmount(original) {
    const m = original.match(/\d[\d,]*(?:\.\d+)?/);
    if (!m) return this._reshapeDigits(original);
    const raw = m[0];
    const hasGrouping = raw.includes(",");
    const hasCents = raw.includes(".");
    const value = parseFloat(raw.replace(/,/g, ""));
    const factor = this._int(60, 175) / 100; // 0.60x .. 1.75x
    let newValue = Math.max(1, Math.round(value * factor));
    let rendered;
    if (hasCents) {
      rendered = hasGrouping
        ? newValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : newValue.toFixed(2);
    } else {
      rendered = hasGrouping ? Math.round(newValue).toLocaleString("en-US") : String(Math.round(newValue));
    }
    return original.slice(0, m.index) + rendered + original.slice(m.index + raw.length);
  }

  _shiftDate(original) {
    // Supported shapes (mirrors the desktop formats):
    //   January 5, 2024 | Jan 5, 2024 | 5 January 2024 | 5th January 2024
    //   01/05/2024 | 1/5/24 | 2024-01-05 | January 2024 | 2024
    let m;
    if ((m = original.match(/^([A-Za-z]+)\.?\s+(\d{1,2})(st|nd|rd|th)?,\s*(\d{4})$/))) {
      const mo = MONTHS[m[1].toLowerCase()];
      if (!mo) return null;
      return this._render(m[1], +m[2], m[3] || "", +m[4], original, "us");
    }
    if ((m = original.match(/^(\d{1,2})(st|nd|rd|th)?\s+([A-Za-z]+)\.?\s+(\d{4})$/))) {
      const mo = MONTHS[m[3].toLowerCase()];
      if (!mo) return null;
      return this._render(m[3], +m[1], m[2] || "", +m[4], original, "uk");
    }
    if ((m = original.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/))) {
      let year = +m[3];
      if (year < 100) year += year < 50 ? 2000 : 1900;
      const d = new Date(Date.UTC(year, +m[1] - 1, +m[2]));
      if (isNaN(d.getTime()) || d.getUTCMonth() !== +m[1] - 1) return null;
      d.setUTCDate(d.getUTCDate() + this.dateDelta);
      const pad = (n) => String(n).padStart(2, "0");
      return pad(d.getUTCMonth() + 1) + "/" + pad(d.getUTCDate()) + "/" +
        (m[3].length === 2 ? String(d.getUTCFullYear()).slice(2) : d.getUTCFullYear());
    }
    if ((m = original.match(/^(\d{4})-(\d{2})-(\d{2})$/))) {
      const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
      if (isNaN(d.getTime())) return null;
      d.setUTCDate(d.getUTCDate() + this.dateDelta);
      const pad = (n) => String(n).padStart(2, "0");
      return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate());
    }
    if ((m = original.match(/^([A-Za-z]+)\.?\s+(\d{4})$/))) {
      const mo = MONTHS[m[1].toLowerCase()];
      if (!mo) return null;
      // Shift by whole months (|dateDelta| >= 30 days, so at least one).
      const months = Math.sign(this.dateDelta) * Math.max(1, Math.round(Math.abs(this.dateDelta) / 30.44));
      const total = +m[2] * 12 + (mo - 1) + months;
      return this._monthName(m[1], (total % 12) + 1) + " " + Math.floor(total / 12);
    }
    if ((m = original.match(/^\d{4}$/))) {
      return String(+original + (Math.abs(this.dateDelta) > 300 ? Math.sign(this.dateDelta) : 1));
    }
    return null;
  }

  _monthName(spelled, num) {
    // Keep the abbreviation style of the original (Jan vs January).
    const full = ["January","February","March","April","May","June","July",
      "August","September","October","November","December"][num - 1];
    // A spelled-out original ("June") stays spelled out; "Jun"/"Sept" abbreviate.
    const isFull = spelled.length > 3 && full.toLowerCase().startsWith(spelled.toLowerCase()) &&
      spelled.length === full.length;
    return isFull ? full : full.slice(0, 3);
  }

  _render(monthSpelled, day, suffix, year, original, style) {
    const d = new Date(Date.UTC(year, MONTHS[monthSpelled.toLowerCase()] - 1, day));
    if (isNaN(d.getTime())) return null;
    d.setUTCDate(d.getUTCDate() + this.dateDelta);
    const num = d.getUTCDate();
    const mo = this._monthName(monthSpelled, d.getUTCMonth() + 1);
    const y = d.getUTCFullYear();
    const dayStr = original.match(/\d{1,2}/)[0].length === 2 && num < 10
      ? "0" + num : String(num);
    if (style === "us") return mo + " " + dayStr + suffix + ", " + y;
    return dayStr + suffix + " " + mo + " " + y;
  }

  _generate(entityType, original) {
    switch (entityType) {
      case "PERSON":
        // A lone name is most often a surname ("Mrs Smith"); a surname
        // stand-in reads naturally either way.
        return original.split(NAME_SPLIT).length === 1
          ? this._pick(PERSON_SURNAMES)
          : this._personName();
      case "ORGANIZATION": {
        const suffix = original.match(
          /\b(Foundation|Trust|Fund|Charity|Charities|Association|Society|CIC|University|College|Hospital|Church|School|Academy|Council)\b/
        );
        return this._pick(LAST_NAMES) + " " + (suffix ? suffix[1] : this._pick(ORG_SUFFIXES));
      }
      case "EMAIL_ADDRESS": {
        const first = this._pick(FIRST_NAMES).toLowerCase();
        const last = this._pick(LAST_NAMES).toLowerCase();
        return first + "." + last + this._int(10, 99) + "@example.com";
      }
      case "PHONE_NUMBER": return this._reshapeDigits(original);
      case "DATE_TIME": {
        const shifted = this._shiftDate(original);
        return shifted !== null ? shifted : this._personName() && "March " + this._int(1, 28) + ", " + this._int(2020, 2026);
      }
      case "LOCATION": return this._location(original);
      case "UK_NINO": return this._reshapeAlnum(original);
      case "SORT_CODE":
      case "BANK_ACCOUNT": return this._reshapeDigits(original);
      case "URL": return "https://www.example.org/" + this._pick(LAST_NAMES).toLowerCase();
      case "US_SSN": return this._reshapeDigits(original);
      case "CREDIT_CARD": return this._reshapeDigits(original);
      case "IBAN_CODE": return this._reshapeAlnum(original);
      case "DONATION_AMOUNT": return this._reshapeAmount(original);
      case "WEALTH_RATING":
        return /\d/.test(original) ? this._reshapeDigits(original) : this._reshapeAlnum(original);
      case "CONSTITUENT_ID":
      case "FUND_CODE": return this._reshapeAlnum(original);
      default: return this._pick(LAST_NAMES);
    }
  }
}

/* ------------------------------------------------------------------ */
/* Apply / reverse                                                    */
/* ------------------------------------------------------------------ */

function applyReplacements(text, replacements) {
  // Spans never overlap (selectSpans), so one left-to-right pass is safe and
  // linear; re-slicing the whole string per span froze on large documents.
  const sorted = replacements.slice().sort((a, b) => a[0].start - b[0].start);
  const pieces = [];
  let cursor = 0;
  for (const [span, penName] of sorted) {
    pieces.push(text.slice(cursor, span.start), penName);
    cursor = span.end;
  }
  pieces.push(text.slice(cursor));
  return pieces.join("");
}

function reverseText(text, entries) {
  if (!entries.length) return text;
  // Leftmost, longest-first matching (same result as a longest-first regex
  // alternation). Stand-ins are bucketed by their first two characters: a
  // single alternation of thousands of stand-ins costs text × stand-ins.
  const lookup = new Map(entries.filter((e) => e.pen_name).map((e) => [e.pen_name, e.original]));
  const buckets = new Map();
  for (const pen of lookup.keys()) {
    const k = pen.slice(0, 2);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(pen);
  }
  for (const list of buckets.values()) list.sort((a, b) => b.length - a.length);
  const out = [];
  let last = 0;
  let i = 0;
  while (i < text.length) {
    const candidates = (buckets.get(text.slice(i, i + 2)) || []).concat(buckets.get(text[i]) || []);
    const pen = candidates.find((p) => text.startsWith(p, i));
    if (pen === undefined) { i++; continue; }
    out.push(text.slice(last, i), lookup.get(pen));
    i += pen.length;
    last = i;
  }
  out.push(text.slice(last));
  return out.join("");
}

/* ------------------------------------------------------------------ */
/* Session (mirrors PennameSession)                                   */
/* ------------------------------------------------------------------ */

const MAX_VERIFY_ATTEMPTS = 5;

class PennameSession {
  constructor(seed) {
    this.generator = new PenNameGenerator(seed);
    this.ignored = new Set();      // "type|value"
    this.customValues = new Map(); // value -> type
  }

  ignoreValue(entityType, original) { this.ignored.add(entityType + "|" + original); }
  unignoreValue(entityType, original) { this.ignored.delete(entityType + "|" + original); }

  setPenName(entityType, original, penName) {
    if (!penName || !penName.trim()) throw new Error("a pen name cannot be empty");
    if (penName === original) throw new Error("a pen name must be different from the real value");
    this.generator.pinPenName(entityType, original, penName.trim());
  }

  alwaysReplace(value, entityType) {
    if (!value || !value.trim()) throw new Error("cannot add an empty value");
    this.customValues.set(value, entityType || "CUSTOM");
  }

  collectSpans(text) {
    let spans = text.trim() ? detectSpans(text) : [];
    // Headings and labels are not donor data.
    // Headings and labels are not donor data — but a titled name
    // ("Kind regards, Mr Dorothy Marlowe.") must be trimmed to the real
    // name, not dropped: the title words are on the noise list.
    spans = spans.flatMap((s) => {
      if (s.entity_type !== "PERSON" || personLooksReal(s.text)) return [s];
      // k may reach the last word: "Mrs Smith" keeps "Smith".
      const words = s.text.split(/\s+/);
      for (let k = 1; k < words.length; k++) {
        const sub = words.slice(k).join(" ");
        if (personLooksReal(sub)) {
          const off = s.text.indexOf(sub);
          return [{ ...s, start: s.start + off, end: s.start + off + sub.length, text: sub }];
        }
      }
      return [];
    });
    for (const [value, type] of this.customValues) {
      const esc = value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const re = new RegExp(esc, "g");
      let m;
      while ((m = re.exec(text)) !== null) {
        spans.push({ start: m.index, end: m.index + value.length, entity_type: type, score: 1.0, text: value });
      }
    }
    spans = spans.filter((s) => !this.ignored.has(s.entity_type + "|" + s.text));
    return selectSpans(spans);
  }

  pseudonymize(text) {
    return this._pseudonymizeSpans(text, this.collectSpans(text));
  }

  _pseudonymizeSpans(text, spans) {
    if (!spans.length) return { text, entries: [] };
    for (let attempt = 0; attempt < MAX_VERIFY_ATTEMPTS; attempt++) {
      // Full names first, so a bare surname can reuse its person's stand-in.
      for (const span of spans) {
        if (span.entity_type === "PERSON" && span.text.split(NAME_SPLIT).length > 1) {
          this.generator.penNameFor(span.entity_type, span.text, text);
        }
      }
      const replacements = spans.map((span) => [
        span,
        this.generator.penNameFor(span.entity_type, span.text, text),
      ]);
      const seen = new Map();
      for (const [s, pen] of replacements) {
        seen.set(s.entity_type + "|" + s.text, {
          original: s.text, pen_name: pen, entity_type: s.entity_type, score: s.score,
        });
      }
      const entries = [...seen.values()];
      const newText = applyReplacements(text, replacements);
      // Self-verification: the round trip must hold before we return.
      if (reverseText(newText, entries) === text) {
        return { text: newText, entries };
      }
      for (const span of spans) this.generator.forget(span.entity_type, span.text);
    }
    throw new PenNameError("could not produce a reversible pseudonymization for this document");
  }

  reverse(text, entries) {
    return reverseText(text, entries);
  }
}

/* ------------------------------------------------------------------ */
/* .pnmap encryption (WebCrypto AES-256-GCM, PBKDF2-SHA256)           */
/* ------------------------------------------------------------------ */
/* Framing: "PNMAP" | 0x02 | salt(16) | iv(12) | ciphertext.
 * The magic+version bytes are the AAD, as on desktop. Version 2 marks the
 * passphrase-derived mobile format (desktop v1 keys live in the OS keychain). */

const PNMAP_MAGIC = new Uint8Array([0x50, 0x4e, 0x4d, 0x41, 0x50]); // "PNMAP"
const PNMAP_VERSION = 2;
const PBKDF2_ITERATIONS = 310000;

function aad() {
  const out = new Uint8Array(PNMAP_MAGIC.length + 1);
  out.set(PNMAP_MAGIC, 0);
  out[PNMAP_MAGIC.length] = PNMAP_VERSION;
  return out;
}

async function deriveKey(passphrase, salt) {
  const material = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

async function encryptMapping(mappingDict, passphrase) {
  if (!passphrase) throw new Error("a passphrase is required to encrypt the key file");
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(passphrase, salt);
  const plaintext = new TextEncoder().encode(JSON.stringify(mappingDict));
  const ciphertext = new Uint8Array(
    await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad() }, key, plaintext)
  );
  const out = new Uint8Array(PNMAP_MAGIC.length + 1 + salt.length + iv.length + ciphertext.length);
  out.set(aad(), 0);
  out.set(salt, PNMAP_MAGIC.length + 1);
  out.set(iv, PNMAP_MAGIC.length + 1 + salt.length);
  out.set(ciphertext, PNMAP_MAGIC.length + 1 + salt.length + iv.length);
  return out;
}

/** Decrypt and return the full mapping dict (including any extra fields
 *  such as doc_hash) without reducing it to entries. */
async function decryptMappingRaw(blob, passphrase) {
  const headerLen = PNMAP_MAGIC.length + 1 + 16 + 12;
  const bytes = blob instanceof Uint8Array ? blob : new Uint8Array(blob);
  if (bytes.length < headerLen) throw new Error("this file is not a Penname mapping file");
  for (let i = 0; i < PNMAP_MAGIC.length; i++) {
    if (bytes[i] !== PNMAP_MAGIC[i]) throw new Error("this file is not a Penname mapping file");
  }
  if (bytes[PNMAP_MAGIC.length] !== PNMAP_VERSION) {
    throw new Error("unsupported mapping file version");
  }
  const salt = bytes.slice(PNMAP_MAGIC.length + 1, PNMAP_MAGIC.length + 17);
  const iv = bytes.slice(PNMAP_MAGIC.length + 17, headerLen);
  const key = await deriveKey(passphrase, salt);
  let plaintext;
  try {
    plaintext = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv, additionalData: aad() }, key, bytes.slice(headerLen)
    );
  } catch (e) {
    throw new Error("could not unlock this mapping file — wrong passphrase or damaged file");
  }
  const dict = JSON.parse(new TextDecoder().decode(plaintext));
  if (!dict || dict.version !== 1) throw new Error("unsupported mapping version");
  return dict;
}

async function decryptMapping(blob, passphrase) {
  const headerLen = PNMAP_MAGIC.length + 1 + 16 + 12;
  const bytes = blob instanceof Uint8Array ? blob : new Uint8Array(blob);
  if (bytes.length < headerLen) throw new Error("this file is not a Penname mapping file");
  for (let i = 0; i < PNMAP_MAGIC.length; i++) {
    if (bytes[i] !== PNMAP_MAGIC[i]) throw new Error("this file is not a Penname mapping file");
  }
  const version = bytes[PNMAP_MAGIC.length];
  if (version !== PNMAP_VERSION) {
    throw new Error(
      version === 1
        ? "this key file was made by the desktop app — enter the passphrase you set in Penname Mobile"
        : "unsupported mapping file version: " + version
    );
  }
  const salt = bytes.slice(PNMAP_MAGIC.length + 1, PNMAP_MAGIC.length + 17);
  const iv = bytes.slice(PNMAP_MAGIC.length + 17, headerLen);
  const ciphertext = bytes.slice(headerLen);
  const key = await deriveKey(passphrase, salt);
  let plaintext;
  try {
    plaintext = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv, additionalData: aad() }, key, ciphertext
    );
  } catch (e) {
    throw new Error("could not unlock this mapping file — wrong passphrase or damaged file");
  }
  return mappingFromDict(JSON.parse(new TextDecoder().decode(plaintext)));
}

/* ------------------------------------------------------------------ */

const PennameEngine = {
  PennameSession, PenNameGenerator, PenNameError,
  detectSpans, selectSpans, applyReplacements, reverseText,
  mappingToDict, mappingFromDict, encryptMapping, decryptMapping, decryptMappingRaw,
};

if (typeof module !== "undefined" && module.exports) module.exports = PennameEngine;
if (typeof window !== "undefined") window.PennameEngine = PennameEngine;
