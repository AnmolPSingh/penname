/* Penname Activity log — encrypted, metadata-only, local-only.
 *
 * Design (agreed in brainstorm):
 *   - Logs METADATA only: action, document name, content hash, per-type
 *     counts, key-file name. NEVER original values, pen names, or text.
 *   - Every event is encrypted at rest with a non-extractable AES-GCM key
 *     that lives in IndexedDB — the log is unreadable outside the app.
 *   - The user can see everything (Activity view), clear it in one tap,
 *     or export it as CSV for compliance evidence.
 *   - The content hash links Protect ↔ Restore: the app can tell the user
 *     which protected document a key file belongs to.
 */
"use strict";

const Activity = (() => {
  const DB_NAME = "penname";
  const DB_VERSION = 1;
  const EVENTS = "events";
  const KEYS = "keys";
  const KEY_NAME = "device";

  let dbPromise = null;

  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(EVENTS)) db.createObjectStore(EVENTS, { keyPath: "id" });
        if (!db.objectStoreNames.contains(KEYS)) db.createObjectStore(KEYS, { keyPath: "name" });
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    return dbPromise;
  }

  function tx(store, mode, fn) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          const t = db.transaction(store, mode);
          const s = t.objectStore(store);
          const out = fn(s);
          t.oncomplete = () => resolve(out && out.result !== undefined ? out.result : out);
          t.onerror = () => reject(t.error);
        })
    );
  }

  /* --- device key (non-extractable, generated once) ---------------- */

  async function getDeviceKey() {
    const db = await openDb();
    const existing = await new Promise((resolve, reject) => {
      const t = db.transaction(KEYS, "readonly");
      const req = t.objectStore(KEYS).get(KEY_NAME);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    if (existing && existing.key) return existing.key;
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, [
      "encrypt",
      "decrypt",
    ]);
    await new Promise((resolve, reject) => {
      const t = db.transaction(KEYS, "readwrite");
      t.objectStore(KEYS).put({ name: KEY_NAME, key });
      t.oncomplete = resolve;
      t.onerror = () => reject(t.error);
    });
    return key;
  }

  /* --- crypto helpers ---------------------------------------------- */

  async function encryptJson(obj) {
    const key = await getDeviceKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt(
      { name: "AES-GCM", iv },
      key,
      new TextEncoder().encode(JSON.stringify(obj))
    );
    return { iv, ct: new Uint8Array(ct) };
  }

  async function decryptBlob(record) {
    const key = await getDeviceKey();
    const pt = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: record.iv },
      key,
      record.ct
    );
    return JSON.parse(new TextDecoder().decode(pt));
  }

  /* --- public API --------------------------------------------------- */

  /** SHA-256 of the document text, first 16 hex chars. Identifies a
   *  document without storing any of its content. */
  async function contentHash(text) {
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(digest).slice(0, 8)]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  /** Record an event. `data` must contain metadata only. */
  async function log(action, data) {
    try {
      const { iv, ct } = await encryptJson({ action, ts: Date.now(), ...data });
      const id = crypto.randomUUID();
      await tx(EVENTS, "readwrite", (s) => s.put({ id, iv, ct }));
    } catch (e) {
      /* Logging must never break the app (e.g. private browsing). */
      console.warn("activity log unavailable:", e);
    }
  }

  /** All events, newest first. */
  async function all() {
    const db = await openDb();
    const records = await new Promise((resolve, reject) => {
      const t = db.transaction(EVENTS, "readonly");
      const req = t.objectStore(EVENTS).getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
    const events = [];
    for (const r of records) {
      try {
        events.push(await decryptBlob(r));
      } catch (e) {
        /* skip undecryptable (should not happen) */
      }
    }
    return events.sort((a, b) => b.ts - a.ts);
  }

  /** Erase everything. Immediate and irreversible. */
  async function clear() {
    await tx(EVENTS, "readwrite", (s) => s.clear());
  }

  /** CSV export for compliance evidence. */
  async function csv() {
    const events = await all();
    const esc = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
    const rows = [["date", "action", "document", "content_hash", "details", "key_file"]];
    for (const e of events) {
      rows.push([
        new Date(e.ts).toISOString(),
        e.action,
        e.doc || "",
        e.hash || "",
        e.details || "",
        e.keyFile || "",
      ]);
    }
    return rows.map((r) => r.map(esc).join(",")).join("\r\n");
  }

  return { log, all, clear, csv, contentHash };
})();

if (typeof window !== "undefined") window.Activity = Activity;