# Website text for the App Store listing

Both pages are **live** as of 5 October 2026 (philanthropel.com v1.7.0):

- Support URL: https://philanthropel.com/support
- Privacy Policy URL: https://philanthropel.com/privacy (now has a
  "The Penname app" section)

The published wording is in the website project (`app/support/page.tsx`,
`app/privacy/page.tsx` and their markdown mirrors in `public/md/`). The text
below is the draft it was written from, kept for reference. Contact address
used on the site: info@philanthropel.com.

---

## 1. Support page — philanthropel.com/support

### Penname support

Penname gives private details a pen name before you share a document with an
AI assistant, and brings the real details back afterwards. Everything happens
on your device.

**Get help:** email info@philanthropel.com. Every message is read and answered by a person. Please do not send us donor data or key
files — we never need them to help you.

#### Common questions

**I forgot my passphrase. Can you recover it?**
No. The passphrase never leaves your device and we have no copy. Without it
the key file cannot be opened. Protect the document again and choose a
passphrase you will remember.

**I lost my key file.**
The key file (.pnmap) is the only record of which stand-in belongs to which
real detail. Without it, the real details cannot be put back automatically.
Protect the original document again to make a new safe copy and key file.

**Where is my key file?**
When you tap "Save key file", iOS shows the share sheet. Choose "Save to
Files" and pick a folder. Open the Files app to find it later.

**Penname missed something.**
No tool finds everything. On the review screen, type the exact text into
"Penname missed something? Add it here" and it will be replaced everywhere.
Always read the safe copy once before you share it.

**A restored detail looks wrong.**
Every detail Penname puts back is highlighted. If your assistant reused a
stand-in for something new — the same amount in a different sentence, for
example — Penname cannot tell the difference and restores it. Check the
highlighted values. Anything Penname was unsure about is listed above the
text and left unchanged.

**Does Penname make us GDPR compliant?**
No. Because the real details can be restored, the safe copy still counts as
personal data. Penname reduces how much personal data you share with an AI
assistant; it is a safeguard, not a compliance tool or legal advice.

**Which files can I open?**
Pasted text, and .txt, .md and .csv files up to about 1 MB of text.

**Can I open key files from the desktop app?**
Not yet. Desktop key files are locked to that computer's keychain; the
iPhone and iPad app uses a passphrase instead.

---

## 2. Privacy policy — section to add to philanthropel.com/privacy

### Penname app (iPhone and iPad)

**We collect nothing.** Penname has no accounts, no analytics, no advertising
and no tracking. The app does not connect to the internet: it sends no data
to Philanthropel or to anyone else.

**Your documents stay on your device.** Text you paste or open is processed
in the app's memory on your device and is not stored by the app. Closing the
app clears it.

**Key files.** The key file that restores the real details is encrypted on
your device with a passphrase you choose (AES-256), and is saved only where
you choose to save it. We never receive the key file or the passphrase and
cannot recover either.

**Activity log.** The app keeps a private log on your device of what you
protected and restored: the document name, the date, and how many details
were replaced. It never records the details themselves. The log is encrypted
on the device; you can export it or erase it at any time from the Activity
tab.

**What you share is your choice.** The only thing that leaves your device is
what you choose to copy, share or save — normally the safe copy you paste
into an AI assistant. That assistant's own privacy policy applies to what
you paste into it.

**Children.** Penname is a workplace tool and is not directed at children.

**Contact.** info@philanthropel.com · Philanthropel Limited, registered in
Scotland, company number SC895988.

*Last updated: 5 October 2026.*
