/* Quick engine smoke tests (run: node test_engine.js) */
const E = require("./engine.js");

let failures = 0;
function check(name, cond) {
  if (cond) console.log("  ok  " + name);
  else { console.log("FAIL  " + name); failures++; }
}

const letter = `Dear Margaret Wilson,

Thank you for your generous gift of $25,000 to the Hartley Foundation on March 5, 2024.
Your monthly donation of $1,250.00 has helped 340 families this year.

You can reach me at jane.smith@hartley.org or on +1 (555) 214-8890.
Our offices are at 42 Elm Street, Springfield.
Her donor reference is C-10041 and her fund code is FUND:GEN-2044.

Warm regards,
Jane Smith
Development Director`;

// 1. Detection finds the key entity types
const spans = E.detectSpans(letter);
const types = new Set(spans.map((s) => s.entity_type));
check("detects email", types.has("EMAIL_ADDRESS"));
check("detects amount", types.has("DONATION_AMOUNT"));
check("detects date", types.has("DATE_TIME"));
check("detects phone", types.has("PHONE_NUMBER"));
check("detects org", types.has("ORGANIZATION"));
check("detects constituent id", types.has("CONSTITUENT_ID"));
check("detects street address", types.has("LOCATION"));

// 2. Round trip holds
const session = new E.PennameSession(42);
const result = session.pseudonymize(letter);
check("round trip restores original", session.reverse(result.text, result.entries) === letter);
check("safe copy has no real email", !result.text.includes("jane.smith@hartley.org"));
check("safe copy has no real name", !result.text.includes("Margaret Wilson"));
check("safe copy has no real amount", !result.text.includes("$25,000"));

// 3. Consistency: same value -> same pen name across documents
const doc2 = "Margaret Wilson gave again. Email jane.smith@hartley.org for details.";
const r2 = session.pseudonymize(doc2);
const mw1 = result.entries.find((e) => e.original === "Margaret Wilson");
const mw2 = r2.entries.find((e) => e.original === "Margaret Wilson");
check("consistent pen names across docs", mw1 && mw2 && mw1.pen_name === mw2.pen_name);

// 4. Review actions
const s3 = new E.PennameSession(42);
s3.ignoreValue("EMAIL_ADDRESS", "jane.smith@hartley.org");
const r3 = s3.pseudonymize(letter);
check("ignored value keeps real text", r3.text.includes("jane.smith@hartley.org"));
const s4 = new E.PennameSession(42);
s4.setPenName("PERSON", "Margaret Wilson", "Dorothy Fields");
const r4 = s4.pseudonymize(letter);
check("pinned pen name used", r4.text.includes("Dorothy Fields"));
check("pinned round trip", s4.reverse(r4.text, r4.entries) === letter);

// 5. Custom values
const s5 = new E.PennameSession(42);
s5.alwaysReplace("340 families");
const r5 = s5.pseudonymize(letter);
check("custom value replaced", !r5.text.includes("340 families"));
check("custom round trip", s5.reverse(r5.text, r5.entries) === letter);

// 6. Mapping schema matches desktop v1
const dict = E.mappingToDict(r4.entries);
check("mapping version 1", dict.version === 1);
check("entry shape", dict.entries[0].original !== undefined && dict.entries[0].pen_name !== undefined);
const back = E.mappingFromDict(JSON.parse(JSON.stringify(dict)));
check("mapping serialises/deserialises", JSON.stringify(back) === JSON.stringify(dict.entries));

// 7. Encrypted key file round trip (WebCrypto)
(async () => {
  const blob = await E.encryptMapping(dict, "correct horse battery staple");
  check("pnmap magic present", blob[0] === 0x50 && blob[1] === 0x4e && blob[4] === 0x50);
  check("pnmap version 2", blob[5] === 2);
  const entries = await E.decryptMapping(blob, "correct horse battery staple");
  check("decrypt returns entries", entries.length === dict.entries.length);
  let wrongPassFailed = false;
  try { await E.decryptMapping(blob, "wrong passphrase"); }
  catch (e) { wrongPassFailed = true; }
  check("wrong passphrase rejected", wrongPassFailed);

  // 8. Reverse restores AI reply
  const aiReply = "Here is a thank-you draft for Dorothy Fields mentioning her gift of " +
    (r4.entries.find((e) => e.original === "$25,000") || {}).pen_name + ".";
  const restored = s4.reverse(aiReply, r4.entries);
  check("reverse restores real values into AI reply", restored.includes("Margaret Wilson"));

  // 9. Fuzz: 200 random-ish documents always round-trip
  const words = ["Margaret", "Wilson", "gave", "$5,000", "on", "March 5, 2024", "call",
    "+44 20 7946 0958", "email", "a.b@example.org", "ref", "C-10041", "to", "the",
    "Hartley Foundation", "at", "12 Oak Road", "sincerely", "Jane Smith", "£1,250.50",
    "2024-06-01", "5 June 2024", "https://donate.example.org", "4111 1111 1111 1111"];
  let fuzzOk = true;
  for (let i = 0; i < 200; i++) {
    const doc = Array.from({ length: 8 + (i % 12) }, () =>
      words[Math.floor(Math.random() * words.length)]).join(" ") + ".";
    try {
      const s = new E.PennameSession();
      const r = s.pseudonymize(doc);
      if (s.reverse(r.text, r.entries) !== doc) { fuzzOk = false; console.log("fuzz fail:", doc); break; }
    } catch (e) { fuzzOk = false; console.log("fuzz error:", e.message, "|", doc); break; }
  }
  check("fuzz: 200 docs round-trip", fuzzOk);

  // 10. Wider detection: real data that used to survive into the safe copy
  const leaks = [
    ["apostrophe surname", "We met Patrick O'Brien last week.", ["O'Brien"]],
    ["Mc surname", "We met Fiona McDonald last week.", ["McDonald"]],
    ["accented name", "We met José García last week.", ["José", "García"]],
    ["three-part name", "We met Mary Anne Whitcombe today.", ["Whitcombe"]],
    ["ALL-CAPS name", "DONOR: JANE SMITH gave generously.", ["JANE SMITH"]],
    ["initial + surname", "Signed, J. Smith", ["Smith"]],
    ["name part reused", "Dear Jane Smith,\nWe hope the Smith family is well. Jane, see you soon.", ["Smith", "Jane"]],
    ["name across a line break", "Regards\nJane Smith\nDirector of Giving", ["Jane Smith"]],
    ["title followed by a greeting", "Thanks, Mrs Wilson Dear Jane Smith, hello", ["Wilson", "Jane", "Smith"]],
    ["names side by side", "the Jane Smith Jane Smith Margaret.", ["Jane", "Smith", "Margaret"]],
    ["lone first name", "Thanks to Margaret for her gift.", ["Margaret"]],
    ["lone first name at sentence start", "Siobhan called about the legacy.", ["Siobhan"]],
    ["city", "He moved to Manchester in May.", ["Manchester"]],
    ["city after an address", "12 High Street, Bristol BS1 4DJ.", ["Bristol"]],
    ["amount with a currency code", "A gift of 10,000 GBP arrived.", ["10,000"]],
    ["amount in pounds, spelled", "She pledged 2,500 pounds.", ["2,500"]],
    ["currency code first", "Total: USD 12,500.00", ["12,500"]],
    ["dotted date", "Received 05.01.2024.", ["05.01.2024"]],
    ["UK-order slash date", "Born 25/12/1948.", ["25/12/1948"]],
    ["www address", "See www.smithfamilytrust.org for more.", ["smithfamilytrust"]],
    ["UK postcode", "12 High Street, Bristol BS1 4DJ.", ["BS1 4DJ"]],
    ["UK mobile, no spaces", "Call 07700900123 any time.", ["07700900123"]],
    ["international, no spaces", "Call +447700900123 any time.", ["447700900123"]],
    ["UK international landline", "Call +44 20 7946 0958 now.", ["7946", "0958"]],
    ["UK international with (0)", "Call +44 (0)20 7946 0958 now.", ["7946", "0958"]],
    ["UK international mobile", "Call +44 7700 900123 now.", ["7700", "900123"]],
    ["UK national landline", "Call 01632 960123 today.", ["01632", "960123"]],
    ["UK mobile with a space", "Mob 07700 900123.", ["07700", "900123"]],
    ["French number", "Tel +33 1 42 68 53 00.", ["42 68 53"]],
    ["two phones in a row", "+44 20 7946 0958 +44 20 7946 0999", ["0958", "0999"]],
    ["phone then a date", "+44 20 7946 0958 2024-06-01", ["0958", "2024-06-01"]],
    ["NI number", "NI number QQ 12 34 56 C on file.", ["QQ 12 34 56 C"]],
    ["sort code", "Sort code 20-00-00.", ["20-00-00"]],
    ["month and year", "Pledged in January 2024.", ["January 2024"]],
    ["abbreviated month", "DOB 5 Jan 1948.", ["5 Jan 1948"]],
  ];
  for (const [name, text, secrets] of leaks) {
    const s = new E.PennameSession(7);
    let ok = false;
    try {
      const r = s.pseudonymize(text);
      ok = secrets.every((v) => !r.text.includes(v)) && s.reverse(r.text, r.entries) === text;
    } catch (e) { console.log("   ", name, "threw:", e.message); }
    check("no leak: " + name, ok);
  }

  // 11. Name parts reuse the matching half of the full name's stand-in
  const s11 = new E.PennameSession(11);
  const r11 = s11.pseudonymize("Dear Jane Smith, thank you. Mrs Smith's gift arrived.");
  const full11 = r11.entries.find((e) => e.original === "Jane Smith");
  const part11 = r11.entries.find((e) => e.original === "Smith");
  check("surname stand-in matches full-name stand-in",
    full11 && part11 && full11.pen_name.split(" ").pop() === part11.pen_name);

  // 12. Capacity: big documents no longer run out of stand-ins
  const addrDoc = Array.from({ length: 60 }, (_, i) => `${i + 1} Mill Lane`).join("\n");
  let addrOk = false;
  try {
    const s = new E.PennameSession();
    const r = s.pseudonymize(addrDoc);
    addrOk = s.reverse(r.text, r.entries) === addrDoc &&
      r.entries.every((e) => /^\d+ \S.* Lane$/.test(e.pen_name));
  } catch (e) { console.log("    addresses threw:", e.message); }
  check("60 distinct addresses, address-shaped stand-ins", addrOk);

  const fn = ["Alan", "Betty", "Carl", "Dina", "Evan", "Faye", "Gwen", "Hugh"];
  const ln = ["Abbott", "Baines", "Calder", "Dunmore", "Easton", "Farrow", "Garrick", "Hobbs"];
  const names = [];
  for (let i = 0; i < 2500; i++) {
    const a = String.fromCharCode(97 + (i % 26)), b = String.fromCharCode(97 + ((i / 26 | 0) % 26));
    names.push(`${fn[i % 8]}${a}${b} ${ln[(i >> 3) % 8]}${b}${a}`);
  }
  let namesOk = false;
  try {
    const s = new E.PennameSession();
    const doc = names.join(",\n");
    const r = s.pseudonymize(doc);
    namesOk = s.reverse(r.text, r.entries) === doc;
  } catch (e) { console.log("    names threw:", e.message); }
  check("2,500 distinct names", namesOk);

  // 13. Month-year dates always change (used to fail when the shift was small)
  let monthOk = true;
  for (let seed = 0; seed < 60; seed++) {
    try {
      const s = new E.PennameSession(seed);
      const r = s.pseudonymize("Pledged in March 2023.");
      if (r.text.includes("March 2023")) monthOk = false;
    } catch (e) { monthOk = false; }
  }
  check("month-year dates always shift", monthOk);

  // 13b. A shifted date that lands on another date in the document must not
  // exhaust the generator (the session shift is fixed, so plain retries repeat).
  let collideOk = true;
  try {
    const g = new E.PenNameGenerator(1);
    g.dateDelta = -39; // April 22 -> March 14
    const doc = "Received on March 14, 2025. Reception on April 22, 2025.";
    const p = g.penNameFor("DATE_TIME", "April 22, 2025", doc);
    collideOk = p !== "April 22, 2025" && !doc.includes(p);
  } catch (e) { collideOk = false; }
  check("date shift landing on another date still generates", collideOk);
  const gm = new E.PenNameGenerator(1);
  gm.dateDelta = -39;
  check("spelled-out month stays spelled out when the month changes",
    gm.penNameFor("DATE_TIME", "April 22, 2025", "") === "March 14, 2025");
  check("abbreviated month stays abbreviated",
    gm.penNameFor("DATE_TIME", "Apr 22, 2025", "") === "Mar 14, 2025");

  const days = Array.from({ length: 366 }, (_, i) =>
    new Date(Date.UTC(2024, 0, 1 + i)).toISOString().slice(0, 10));
  let yearOk = false;
  try {
    const s = new E.PennameSession();
    const doc = days.join("\n");
    const r = s.pseudonymize(doc);
    yearOk = r.entries.length === 366 && s.reverse(r.text, r.entries) === doc &&
      r.entries.every((e) => !doc.includes(e.pen_name));
  } catch (e) { console.log("    year of dates threw:", e.message); }
  check("a year of daily dates all get stand-ins", yearOk);

  // 13c. An amount must not swallow the next comma-separated column
  const csvSpans = E.detectSpans("Gift,Date\n£25,2024-01-05\n£1,250,2024-02-06");
  check("amount stops at the CSV column boundary",
    csvSpans.some((x) => x.text === "£25") && csvSpans.some((x) => x.text === "£1,250") &&
    csvSpans.filter((x) => x.entity_type === "DATE_TIME").length === 2);

  // 13d. A gift list dense with amounts and dates still exports and round-trips
  const gifts = ["Gift,Date"].concat(Array.from({ length: 400 }, (_, i) =>
    `£${((i + 1) * 25).toLocaleString("en-US")},${days[i % 366]}`)).join("\n");
  let giftsOk = false;
  try {
    const s = new E.PennameSession();
    const r = s.pseudonymize(gifts);
    giftsOk = s.reverse(r.text, r.entries) === gifts &&
      r.entries.filter((e) => e.entity_type === "DONATION_AMOUNT").length === 400;
  } catch (e) { console.log("    gift list threw:", e.message); }
  check("400 distinct amounts with dates in a CSV", giftsOk);

  // 13e. Name parts side by side must not recreate another name's stand-in
  const adj = "at call gave call $5,000 Jane Smith Margaret C-10041 the email $5,000 12 Oak Road Jane Smith at.";
  let adjOk = true;
  for (let i = 0; i < 40; i++) {
    try {
      const s = new E.PennameSession();
      const r = s.pseudonymize(adj);
      if (s.reverse(r.text, r.entries) !== adj || r.text.includes("Jane") || r.text.includes("Smith")) adjOk = false;
    } catch (e) { adjOk = false; }
  }
  check("adjacent name parts round-trip", adjOk);

  // 13f. When the safety check fails on dates, a retry must move the dates
  // (the session shift is fixed, so regenerating repeats the same clash).
  const glued = "Mrs Wilson 2024-06-01 January 2024 5 June 2024 sincerely.";
  let gluedOk = true;
  for (const delta of [180, 181, 182, -180, -181]) {
    try {
      const s = new E.PennameSession(5);
      s.generator.dateDelta = delta;
      const r = s.pseudonymize(glued);
      if (s.reverse(r.text, r.entries) !== glued) gluedOk = false;
    } catch (e) { gluedOk = false; }
  }
  check("date clashes are retried with different dates", gluedOk);

  // 13g. Ordinary words that happen to be names or places stay untouched
  const plain = "We will mark the occasion in May. Reading the report gave us hope. Please bath the dog.";
  check("everyday words are not treated as names or places", E.detectSpans(plain).length === 0);

  const urlDoc = "See www.smithtrust.org. Or https://give.example.net/x, thanks.";
  const urlSpans = E.detectSpans(urlDoc).filter((x) => x.entity_type === "URL").map((x) => x.text);
  check("web address leaves the sentence punctuation alone",
    urlSpans.join("|") === "www.smithtrust.org|https://give.example.net/x");

  // 13h. Dates keep their written shape
  const gd = new E.PenNameGenerator(1);
  gd.dateDelta = 40;
  check("dotted date keeps its shape", gd.penNameFor("DATE_TIME", "05.01.2024", "") === "14.02.2024");
  check("UK-order slash date keeps its shape", gd.penNameFor("DATE_TIME", "25/12/1948", "") === "03/02/1949");

  // 13i. Pathological input finishes quickly (no quadratic regex)
  const t13 = Date.now();
  E.detectSpans("1".repeat(200000));
  E.detectSpans("A-".repeat(100000));
  E.detectSpans("a.".repeat(100000));
  check("long digit/letter runs are scanned in under 2s", Date.now() - t13 < 2000);

  // 14. Restore copes with the ways an AI reshapes stand-ins
  const s14 = new E.PennameSession(3);
  const src14 = "Dear Jane Smith, thank you for the gift of $1,000 on 2024-01-05.";
  const r14 = s14.pseudonymize(src14);
  const pen = (t) => r14.entries.find((e) => e.entity_type === t).pen_name;
  const [pFirst, pLast] = pen("PERSON").split(" ");
  const restoreOf = (reply) => E.reverseDetailed(reply, r14.entries);

  check("restore: first name only", restoreOf(`Dear ${pFirst},`).text === "Dear Jane,");
  check("restore: title + surname", restoreOf(`Mrs ${pLast} agreed.`).text === "Mrs Smith agreed.");
  check("restore: possessive", restoreOf(`${pen("PERSON")}'s gift`).text === "Jane Smith's gift");
  check("restore: upper case", restoreOf(pen("PERSON").toUpperCase()).text === "JANE SMITH");
  const d14 = new Date(pen("DATE_TIME") + "T00:00:00Z");
  const months = ["January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December"];
  const ukDate = `${d14.getUTCDate()} ${months[d14.getUTCMonth()]} ${d14.getUTCFullYear()}`;
  const usDate = `${months[d14.getUTCMonth()]} ${d14.getUTCDate()}, ${d14.getUTCFullYear()}`;
  check("restore: date rewritten UK style", restoreOf(`on ${ukDate}.`).text === "on 5 January 2024.");
  check("restore: date rewritten US style", restoreOf(`on ${usDate}.`).text === "on January 5, 2024.");
  check("restore: stand-in inside a longer number untouched",
    restoreOf(`Total: ${pen("DONATION_AMOUNT")}0 raised.`).text === `Total: ${pen("DONATION_AMOUNT")}0 raised.`);
  check("restore: part of a longer word untouched",
    restoreOf(`${pLast}shire is lovely.`).text === `${pLast}shire is lovely.`);

  const det14 = restoreOf(`Dear ${pFirst}, your ${pen("DONATION_AMOUNT")} gift.`);
  check("restore reports what it changed",
    det14.restored === 2 && det14.segments.filter((g) => g.original !== undefined).map((g) => g.original).join("|") === "Jane|$1,000");

  // Two people whose stand-ins share a first name: "Dear <first>" is ambiguous
  // and must be left alone and reported, never guessed.
  const amb = [
    { original: "Jane Smith", pen_name: "Nora Lockwood", entity_type: "PERSON", score: 1 },
    { original: "Ann Jones", pen_name: "Nora Hollis", entity_type: "PERSON", score: 1 },
  ];
  const a14 = E.reverseDetailed("Dear Nora, and Nora Hollis.", amb);
  check("ambiguous first name left as is and reported",
    a14.text === "Dear Nora, and Ann Jones." && a14.ambiguous.includes("Nora"));

  // Variant-aware restore still round-trips whole documents
  let variantFuzz = true;
  for (let i = 0; i < 100; i++) {
    const doc = Array.from({ length: 8 + (i % 10) }, () =>
      words[Math.floor(Math.random() * words.length)]).join(" ") + ". Jane said hi to Smith.";
    try {
      const s = new E.PennameSession();
      const r = s.pseudonymize(doc);
      if (E.reverseDetailed(r.text, r.entries).text !== doc) { variantFuzz = false; console.log("variant fuzz fail:", doc); break; }
    } catch (e) { variantFuzz = false; console.log("variant fuzz error:", e.message); break; }
  }
  check("fuzz: variant-aware restore round-trips 100 docs", variantFuzz);

  console.log(failures === 0 ? "\nALL TESTS PASSED" : "\n" + failures + " FAILURES");
  process.exit(failures === 0 ? 0 : 1);
})();
