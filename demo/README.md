# Penname demo files

Invented documents for testing Penname. Every name, address, email and
reference is made up; the phone numbers are from ranges reserved for fiction.

| File | What it tests |
|---|---|
| `01-donor-letter.txt` | The basic loop: a thank-you letter with a name, amounts, dates, phone, email, address, postcode, IDs and a web address. |
| `02-meeting-notes.md` | Harder names (McDonald, O'Brien, García, a three-part name), several date and amount formats, an NI number, sort code and account number. |
| `03-gift-list.csv` | A 25-row export: many distinct names, emails, phones, addresses, postcodes, amounts and dates. |
| `04-tricky-cases.txt` | Details Penname is known to miss, for practising "add it here" on the review screen. |

## Test steps

1. **Open.** On the Protect tab, tap "Choose a file" and pick `01-donor-letter.txt` (or paste its text).
2. **Find.** Tap "Find private details". Check the list: untick one item, type your own stand-in for another.
3. **Create the safe copy.** Read it: the unticked item should still be real, everything else replaced.
4. **Save the key file.** Type a passphrase twice (8+ characters) and tap "Save key file". On iPhone and iPad choose "Save to Files"; on Mac it goes to Downloads.
5. **Ask an AI assistant.** Copy the safe copy into your assistant with this request:

   > Rewrite this as a warmer thank-you note. Greet the donor by first name only, and write the dates out in full.

6. **Restore.** On the Restore tab, paste the assistant's reply, choose the key file, enter the passphrase, and tap "Bring the real details back". Every restored detail is highlighted; the first name and the reworded dates should come back correctly.
7. **Activity.** The Activity tab should show the protect, key-file and restore entries, with no real details in them.

## Things worth trying

- A wrong passphrase on Restore: it should refuse, clearly.
- Typing with the on-screen keyboard: the page should not jump.
- `03-gift-list.csv`: the review list should be long but responsive.
- `04-tricky-cases.txt`: add the missed items by hand and check the safe copy.

On iPhone or iPad, these files are reachable in the Files app under iCloud
Drive ▸ Desktop ▸ penname ▸ demo, if this Mac's Desktop syncs to iCloud.
