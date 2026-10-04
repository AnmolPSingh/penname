/* Penname Mobile — UI logic. Documents and values live in memory only.
 * The one exception is the Activity log: encrypted, metadata-only records
 * (see activity.js) that the user can view, export or erase. */
"use strict";

const E = window.PennameEngine;
const A = window.Activity;

const TYPE_LABELS = {
  PERSON: "Person",
  ORGANIZATION: "Organisation",
  EMAIL_ADDRESS: "Email",
  PHONE_NUMBER: "Phone",
  LOCATION: "Address or place",
  DATE_TIME: "Date",
  DONATION_AMOUNT: "Amount",
  WEALTH_RATING: "Wealth rating",
  CONSTITUENT_ID: "Constituent ID",
  FUND_CODE: "Fund code",
  URL: "Website",
  US_SSN: "SSN",
  CREDIT_CARD: "Card number",
  IBAN_CODE: "IBAN",
  UK_NINO: "NI number",
  SORT_CODE: "Sort code",
  BANK_ACCOUNT: "Account number",
  CUSTOM: "Custom",
};

/* The macOS app (Tauri) saves downloads straight to the Downloads folder. */
const IS_MAC_APP = !!window.__TAURI_INTERNALS__;
const SAVED_WHERE = IS_MAC_APP ? "Saved to Downloads ✓" : "Saved ✓";

const MIN_PASSPHRASE = 8;
const MAX_DOCUMENT_CHARS = 1000000; // ~1 MB of text; larger files stall a phone

/* In the iOS app (and iOS Safari) a download link does nothing useful, so
 * files go through the system share sheet, which offers "Save to Files".
 * Desktop browsers and the macOS app keep the ordinary download. */
const SHARE_FILES =
  !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()) ||
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

/* ---------------- App state ---------------- */

const state = {
  session: null,
  sourceText: "",
  fileName: null,       // name of the chosen file, if any (metadata only)
  spans: [],            // spans selected for review (with live pen names)
  safeText: "",
  entries: [],          // mapping entries of the last export
  docHash: null,        // sha-256 (16 hex) of the source text — no content
  restoreEntries: null, // raw bytes of the chosen .pnmap
  keyFileName: null,
  _restored: "",
};

const $ = (id) => document.getElementById(id);

/* ---------------- Tabs ---------------- */

function showTab(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll("[data-tab]").forEach((b) => b.classList.remove("active"));
  $("view-" + name).classList.add("active");
  document.querySelectorAll(`[data-tab="${name}"]`).forEach((b) => b.classList.add("active"));
  window.scrollTo(0, 0);
  if (name === "activity") renderActivity();
}

document.querySelectorAll("[data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
});

/* ---------------- Protect: step 1 — input ---------------- */

$("btn-detect").addEventListener("click", () => {
  const text = $("input-text").value;
  if (!text.trim()) { showProtectError("Paste or choose a document first."); return; }
  if (text.length > MAX_DOCUMENT_CHARS) {
    showProtectError("This document is too large to check in one go (over 1 MB of text). Split it into smaller parts.");
    return;
  }
  hideProtectError();
  state.session = new E.PennameSession();
  state.sourceText = text;
  state.spans = uniqueSpans(state.session.collectSpans(text), []);
  if (!state.spans.length) {
    showProtectError("No private details were found. You can still add values to replace below.");
  }
  renderReview();
  $("protect-step1").classList.add("hidden");
  $("protect-step2").classList.remove("hidden");
  $("protect-step3").classList.add("hidden");
});

$("btn-choose-file").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  if (!file) return;
  // Checked before reading, so a huge file is never loaded into memory.
  if (file.size > 2 * MAX_DOCUMENT_CHARS) {
    showProtectError("This file is too large to open here (over 2 MB). Split it into smaller parts.");
    ev.target.value = "";
    return;
  }
  hideProtectError();
  const text = await file.text();
  $("input-text").value = text;
  state.fileName = file.name;
  ev.target.value = "";
});

function showProtectError(msg) {
  for (const id of ["protect-error", "protect-error-2", "protect-error-3"]) {
    const el = $(id);
    el.textContent = msg;
    el.classList.remove("hidden");
  }
}
function hideProtectError() {
  for (const id of ["protect-error", "protect-error-2", "protect-error-3"]) {
    $(id).classList.add("hidden");
  }
}

/* ---------------- Protect: step 2 — review ---------------- */

/** One review row per distinct value. Ticking applies to every occurrence of
 *  a value, so showing each occurrence as its own row let two rows for the
 *  same value disagree — and the last one silently won. `previous` carries
 *  over the user's choices when the list is rebuilt. */
function uniqueSpans(spans, previous) {
  const rows = new Map();
  for (const s of spans) {
    const key = s.entity_type + "|" + s.text;
    const row = rows.get(key);
    if (row) { row.count++; continue; }
    const prev = previous.find((p) => p.entity_type === s.entity_type && p.text === s.text);
    rows.set(key, { ...s, count: 1, included: prev ? prev.included : true, pen: prev ? prev.pen : null });
  }
  return [...rows.values()];
}

function renderReview() {
  const list = $("review-list");
  const query = $("review-search").value.trim().toLowerCase();
  list.innerHTML = "";

  let shown = 0;
  for (const span of state.spans) {
    if (query && !span.text.toLowerCase().includes(query) &&
        !(span.pen || "").toLowerCase().includes(query)) continue;
    shown++;
    const row = document.createElement("div");
    row.className = "entry" + (span.included ? "" : " off");

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = span.included;
    cb.setAttribute("aria-label", "Replace this value");
    cb.addEventListener("change", () => {
      span.included = cb.checked;
      row.classList.toggle("off", !cb.checked);
      updateCount();
    });

    const grow = document.createElement("div");
    grow.className = "grow";

    const orig = document.createElement("div");
    orig.className = "original";
    orig.textContent = span.text;

    const meta = document.createElement("div");
    meta.className = "meta";
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = TYPE_LABELS[span.entity_type] || span.entity_type;
    const conf = document.createElement("span");
    conf.className = "confidence";
    conf.textContent = Math.round(span.score * 100) + "% sure";
    meta.append(chip, conf);
    if (span.count > 1) {
      const times = document.createElement("span");
      times.className = "confidence";
      times.textContent = `appears ${span.count} times`;
      meta.append(times);
    }

    const pen = document.createElement("input");
    pen.type = "text";
    pen.className = "pen-input";
    pen.placeholder = "Your own stand-in (optional)";
    pen.value = span.pen || "";
    pen.setAttribute("aria-label", "Stand-in for " + span.text);
    pen.addEventListener("input", () => { span.pen = pen.value; });

    grow.append(orig, meta, pen);
    row.append(cb, grow);
    list.append(row);
  }

  if (!shown) {
    const empty = document.createElement("p");
    empty.className = "count-line";
    empty.textContent = query ? "Nothing matches that search." : "Nothing to review.";
    list.append(empty);
  }
  updateCount();
}

function updateCount() {
  const total = state.spans.length;
  const on = state.spans.filter((s) => s.included).length;
  $("review-count").innerHTML =
    `<strong>${on}</strong> of <strong>${total}</strong> details will be given pen names.`;
}

$("review-search").addEventListener("input", renderReview);

$("btn-tick-shown").addEventListener("click", () => {
  setShown(true);
});
$("btn-untick-shown").addEventListener("click", () => {
  setShown(false);
});
function setShown(value) {
  const query = $("review-search").value.trim().toLowerCase();
  for (const span of state.spans) {
    if (!query || span.text.toLowerCase().includes(query)) span.included = value;
  }
  renderReview();
}

$("btn-add-value").addEventListener("click", () => {
  const input = $("add-value-input");
  const value = input.value.trim();
  if (!value) return;
  try {
    state.session.alwaysReplace(value);
  } catch (e) { showProtectError(e.message); return; }
  input.value = "";
  // Re-collect so the custom value appears alongside detected spans.
  state.spans = uniqueSpans(state.session.collectSpans(state.sourceText), state.spans);
  renderReview();
});

$("btn-back-input").addEventListener("click", () => {
  $("protect-step2").classList.add("hidden");
  $("protect-step1").classList.remove("hidden");
});

/* ---------------- Protect: step 3 — export ---------------- */

$("btn-export").addEventListener("click", async () => {
  hideProtectError();
  // Push user-typed pen names into the generator so generation respects
  // them, and tell the session which values the user chose to keep real.
  const session = state.session;
  for (const span of state.spans) {
    if (span.included) {
      session.unignoreValue(span.entity_type, span.text);
      if (span.pen && span.pen.trim()) {
        try { session.setPenName(span.entity_type, span.text, span.pen); } catch (e) {
          showProtectError(`Stand-in for “${span.text}”: ${e.message}`);
          return;
        }
      }
    } else {
      session.ignoreValue(span.entity_type, span.text);
    }
  }
  try {
    const result = session.pseudonymize(state.sourceText);
    state.safeText = result.text;
    state.entries = result.entries;
  } catch (e) {
    showProtectError(e.message);
    return;
  }
  // Hash the document (hash only — never the content) so the key file and
  // the Activity log can be matched back to it later.
  state.docHash = await A.contentHash(state.sourceText);
  state.docName = state.fileName || "(pasted text)";
  const countSummary = Object.entries(
    state.entries.reduce((acc, e) => {
      const label = TYPE_LABELS[e.entity_type] || e.entity_type;
      acc[label] = (acc[label] || 0) + 1;
      return acc;
    }, {})
  ).map(([label, n]) => `${n} ${label.toLowerCase()}`).join(", ");
  state.countsSummary = countSummary;

  $("safe-output").textContent = state.safeText;
  $("export-summary").textContent =
    `${state.entries.length} private detail${state.entries.length === 1 ? "" : "s"} replaced. ` +
    `Paste the safe copy into your AI assistant.`;
  $("passphrase").value = "";
  $("passphrase-confirm").value = "";
  state.pendingKey = null;
  $("key-note").classList.add("hidden");
  $("protect-step2").classList.add("hidden");
  $("protect-step3").classList.remove("hidden");

    // One metadata-only line in the log: what, when, how many. No values.
    await Activity.log("protect", {
      doc: state.docName,
      hash: state.docHash,
      details: `${state.entries.length} detail${state.entries.length === 1 ? "" : "s"} replaced`,
      countsSummary: countSummary,
      keyFile: null,
    });
});

$("btn-copy-safe").addEventListener("click", async () => {
  await copyText(state.safeText, $("btn-copy-safe"));
});

$("btn-share-safe").addEventListener("click", async () => {
  if (navigator.share) {
    try { await navigator.share({ title: "Safe copy — Penname", text: state.safeText }); } catch (e) {}
  } else {
    await copyText(state.safeText, $("btn-share-safe"));
  }
});

$("btn-download-safe").addEventListener("click", async () => {
  try {
    const outcome = await saveFile(new Blob([state.safeText], { type: "text/plain" }), "penname-safe-copy.txt");
    if (outcome === "downloaded") flash($("btn-download-safe"), SAVED_WHERE);
  } catch (e) { showProtectError("Could not save the file: " + e.message); }
});

$("btn-download-key").addEventListener("click", async () => {
  const pass = $("passphrase").value;
  if (!pass) { showProtectError("Choose a passphrase — it unlocks this key file later."); return; }
  if (pass.length < MIN_PASSPHRASE) {
    showProtectError(`Use at least ${MIN_PASSPHRASE} characters — a short passphrase is easy to guess.`);
    return;
  }
  if (pass !== $("passphrase-confirm").value) {
    showProtectError("The two passphrases don't match. Type the same passphrase in both boxes.");
    return;
  }
  hideProtectError();
  const note = $("key-note");
  try {
    // Encrypting takes a moment; by then iOS may no longer count the tap as
    // permission to open the share sheet. In that case the finished file is
    // kept and the next tap shares it instantly.
    let file = state.pendingKey && state.pendingKey.pass === pass ? state.pendingKey.blob : null;
    if (!file) {
      // Embed the document hash (no content) so this key file can always be
      // matched back to the document it belongs to.
      const dict = E.mappingToDict(state.entries);
      dict.doc_hash = state.docHash || null;
      dict.doc_name = state.docName || null;
      file = new Blob([await E.encryptMapping(dict, pass)], { type: "application/octet-stream" });
    }
    const outcome = await saveFile(file, "penname-key.pnmap");
    if (outcome === "needs-tap") {
      state.pendingKey = { pass, blob: file };
      note.textContent = "Key file ready — tap the button again to choose where to keep it.";
      note.classList.remove("hidden");
      return;
    }
    if (outcome === "cancelled") return;
    state.pendingKey = null;
    note.textContent = SHARE_FILES
      ? "✓ Key file handed over. If you chose “Save to Files”, it is on this device — keep it with your passphrase."
      : IS_MAC_APP
        ? "✓ Key file saved to your Downloads folder. Keep it somewhere safe, with your passphrase."
        : "✓ Key file saved. Keep it somewhere safe on this device.";
    note.classList.remove("hidden");
    await Activity.log("key-saved", {
      doc: state.docName,
      hash: state.docHash,
      details: `${state.entries.length} details · key file saved`,
      countsSummary: state.countsSummary,
      keyFile: "penname-key.pnmap",
    });
  } catch (e) {
    showProtectError(e.message);
  }
});

$("btn-start-over").addEventListener("click", () => {
  state.session = null; state.sourceText = ""; state.spans = [];
  state.safeText = ""; state.entries = [];
  state.fileName = null; state.docHash = null; state.docName = null;
  state.pendingKey = null;
  $("input-text").value = "";
  $("safe-output").textContent = "";
  $("passphrase").value = "";
  $("passphrase-confirm").value = "";
  $("key-note").classList.add("hidden");
  $("protect-step3").classList.add("hidden");
  $("protect-step1").classList.remove("hidden");
  hideProtectError();
});

/* ---------------- Restore ---------------- */

$("btn-choose-key").addEventListener("click", () => $("key-input").click());
$("key-input").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  if (!file) return;
  state.restoreEntries = new Uint8Array(await file.arrayBuffer());
  state.keyFileName = file.name;
  $("key-file-name").textContent = file.name + " loaded.";
  ev.target.value = "";
});

$("btn-restore").addEventListener("click", async () => {
  const out = $("restore-output");
  const err = $("restore-error");
  err.classList.add("hidden");
  out.textContent = "";
  try {
    if (!state.restoreEntries) throw new Error("Choose your .pnmap key file first.");
    const pass = $("restore-passphrase").value;
    if (!pass) throw new Error("Enter the passphrase for this key file.");
    const raw = await E.decryptMappingRaw(state.restoreEntries, pass);
    const entries = E.mappingFromDict(raw);
    const reply = $("restore-input").value;
    if (!reply.trim()) throw new Error("Paste your assistant's reply first.");
    const result = E.reverseDetailed(reply, entries);
    renderRestored(result);
    $("restore-actions").classList.remove("hidden");
    state._restored = result.text;

    // Match the key file back to the document it came from (hash only).
    let matchNote = "";
    if (raw.doc_hash) {
      const events = await A.all();
      const match = events.find((ev) => ev.action === "protect" && ev.hash === raw.doc_hash);
      if (match) {
        matchNote = `✓ This key file matches “${match.doc}”, protected ${new Date(match.ts).toLocaleDateString()}.`;
      }
    }
    const noteEl = $("restore-match");
    if (noteEl) {
      noteEl.textContent = matchNote;
      noteEl.classList.toggle("hidden", !matchNote);
    }
    await Activity.log("restore", {
      doc: raw.doc_name || "(unknown document)",
      hash: raw.doc_hash || null,
      details: `${result.restored} detail${result.restored === 1 ? "" : "s"} restored`,
      keyFile: state.keyFileName || null,
    });
  } catch (e) {
    err.textContent = e.message;
    err.classList.remove("hidden");
    $("restore-actions").classList.add("hidden");
  }
});

/** Show the restored text with every put-back value highlighted, a count,
 *  and a warning for anything restore deliberately did not guess. */
function renderRestored(result) {
  const out = $("restore-output");
  out.textContent = "";
  for (const seg of result.segments) {
    if (seg.original === undefined) { out.append(seg.text); continue; }
    const mark = document.createElement("mark");
    mark.className = "restored";
    mark.textContent = seg.text;
    mark.title = "Was: " + seg.standIn;
    out.append(mark);
  }
  $("restore-summary").textContent = result.restored
    ? `${result.restored} detail${result.restored === 1 ? "" : "s"} put back — highlighted below. ` +
      "Glance over them: if the reply reused a stand-in for something new, it is highlighted too."
    : "No stand-ins were found in this reply, so nothing was changed. Check it is the reply to the protected document.";
  const warn = $("restore-warning");
  if (result.ambiguous.length) {
    warn.textContent = "Left as is, because it could belong to more than one real person or date: " +
      result.ambiguous.map((a) => `“${a}”`).join(", ") + ". Fix these by hand.";
    warn.classList.remove("hidden");
  } else {
    warn.classList.add("hidden");
  }
}

$("btn-copy-restored").addEventListener("click", async () => {
  await copyText(state._restored || "", $("btn-copy-restored"));
});
$("btn-download-restored").addEventListener("click", async () => {
  try {
    const outcome = await saveFile(new Blob([state._restored || ""], { type: "text/plain" }), "penname-restored.txt");
    if (outcome === "downloaded") flash($("btn-download-restored"), SAVED_WHERE);
  } catch (e) {
    const err = $("restore-error");
    err.textContent = "Could not save the file: " + e.message;
    err.classList.remove("hidden");
  }
});

async function renderActivity() {
  const list = $("activity-list");
  const events = await A.all();
  if (!events.length) {
    list.innerHTML = '<p class="count-line">No activity yet. When you protect or restore a document, a private metadata entry appears here.</p>';
    return;
  }
  list.innerHTML = "";
  for (const ev of events) {
    const row = document.createElement("div");
    row.className = "entry";
    const grow = document.createElement("div");
    grow.className = "grow";
    const title = document.createElement("div");
    title.className = "original";
    title.textContent = (ev.action === "protect" ? "Protected" :
      ev.action === "restore" ? "Restored" : "Key file saved for") + " " + (ev.doc || "");
    const meta = document.createElement("div");
    meta.className = "meta";
    const when = document.createElement("span");
    when.className = "confidence";
    when.textContent = new Date(ev.ts).toLocaleString();
    meta.append(when);
    if (ev.countsSummary) {
      const chip = document.createElement("span");
      chip.className = "chip";
      meta.append(Object.assign(document.createElement("span"), { className: "chip", textContent: ev.countsSummary }));
    }
    grow.append(title, meta);
    row.append(grow);
    list.append(row);
  }
}

$("btn-export-activity").addEventListener("click", async () => {
  const csv = await A.csv();
  try {
    const outcome = await saveFile(new Blob([csv], { type: "text/csv" }), "penname-activity.csv");
    if (outcome === "downloaded") flash($("btn-export-activity"), SAVED_WHERE);
  } catch (e) { alert("Could not save the file: " + e.message); }
});

$("btn-clear-activity").addEventListener("click", async () => {
  if (!confirm("Erase the whole Activity log? This cannot be undone.")) return;
  await A.clear();
  renderActivity();
});

/* ---------------- Helpers ---------------- */

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    // Fallback for older Safari.
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.append(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  flash(btn, "Copied ✓");
}

/** Briefly replace a button's label to confirm an action. */
function flash(btn, label) {
  if (btn.dataset.label) return; // already flashing
  btn.dataset.label = btn.textContent;
  btn.textContent = label;
  setTimeout(() => { btn.textContent = btn.dataset.label; delete btn.dataset.label; }, 1600);
}

/** Save a file the way the platform allows. Resolves to "shared",
 *  "downloaded", "cancelled" (user closed the share sheet) or "needs-tap"
 *  (the share sheet needs a fresh tap). Other failures throw. */
async function saveFile(blob, filename) {
  if (!SHARE_FILES) {
    downloadBlob(blob, filename);
    return "downloaded";
  }
  const file = new File([blob], filename, { type: blob.type || "application/octet-stream" });
  if (!navigator.canShare || !navigator.canShare({ files: [file] })) {
    throw new Error("this device cannot share files");
  }
  try {
    await navigator.share({ files: [file] });
    return "shared";
  } catch (e) {
    if (e.name === "AbortError") return "cancelled";
    if (e.name === "NotAllowedError") return "needs-tap";
    throw e;
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/* ---------------- Init ---------------- */

// The Mac app is sandboxed with no way to open a browser, so the
// Philanthropel credits are shown as plain text there, not dead links.
if (IS_MAC_APP) {
  document.querySelectorAll('a[href^="https://philanthropel.com"]').forEach((a) => {
    a.removeAttribute("href");
    a.removeAttribute("target");
  });
}

showTab("protect");