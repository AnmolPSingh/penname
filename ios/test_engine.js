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
    ["UK postcode", "12 High Street, Bristol BS1 4DJ.", ["BS1 4DJ"]],
    ["UK mobile, no spaces", "Call 07700900123 any time.", ["07700900123"]],
    ["international, no spaces", "Call +447700900123 any time.", ["447700900123"]],
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

  console.log(failures === 0 ? "\nALL TESTS PASSED" : "\n" + failures + " FAILURES");
  process.exit(failures === 0 ? 0 : 1);
})();
