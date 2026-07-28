# Compact Report Format

Use this format for recurring scheduled Telegram/mobile updates. Send the whole update as a single fenced `text` codeblock so Telegram keeps the alignment on mobile. One line per leg — no per-leg Market/Score/Status/Source sub-lines, and no boundary footer (the status-only boundary is stated once at job creation).

```text
⚽️ Acca — <HH:MM timezone> · <emoji> <overall> · <settled>/<total> settled
1) <Home> <score> <Away> · <FT / 45' / KO HH:MM> — <market>: <emoji> <status>
2) <Home> <score> <Away> · <FT / 45' / KO HH:MM> — <market>: <emoji> <status>
Next check: <HH:MM timezone> · ESPN
```

Live example:

```text
⚽️ Acca — 01:00 CEST · 🟢 LIVE · 0/2 settled
1) CRB 2-0 Vila Nova · 29' — CRB win: 🟢 WINNING
2) Sport 0-0 Cuiabá · 31' — Over 1.5: ⏳ PENDING
Next check: 01:15 CEST · ESPN
```

Final example:

```text
⚽️ Acca — 02:30 CEST · ✅ WON · 2/2 settled
1) CRB 2-0 Vila Nova · FT — CRB win: ✅ WON
2) Sport 1-1 Cuiabá · FT — Over 1.5: ✅ WON
TRACKING COMPLETE · ESPN
```

Rules:

- One line per leg, most lines under ~72 characters.
- Leg-status emojis: ✅ won, 🟢 live/winning, ⏳ pending, ❌ lost/dead, ❔ unverifiable, ⚪ void.
- Overall-status emojis: ✅ WON, 🟢 LIVE, 🟡 PARTIAL, ⏳ PENDING, ❌ DEAD, ❔ UNVERIFIABLE.
- The trailing `· ESPN` covers all script-fed legs; only a leg that used a fallback source gets `(via BBC)` etc. appended to its line.
- `Next check` is computed from the actual cron interval — never guess a shorter one.
- Caveats: one short `Note:` line above the last line, e.g. `Note: source dates conflicted; retrying.` Never repeat a caveat per leg.
- `TRACKING COMPLETE` only when every leg is final/settled, Hermes explicitly says the max-repeat run has been reached, or the user stopped tracking.
- No betting advice, predictions, cash-out advice, or odds optimization.

## Send on change, not on schedule

The pre-run script prints `CHANGE SINCE LAST RUN: YES/NO` by comparing each leg's state+score to the previous run:

- `NO` -> respond with the runtime's silent token (`[SILENT]` in Hermes). A live match whose score has not moved is not news; the match clock alone never justifies a message.
- `YES` -> send, unless every changed leg is still `NOT STARTED` (schedule confirmations are covered by the job-creation message).
- Always send when a leg settles or the overall status changes; after the final all-settled report, later runs show no change and stay silent — never re-send a settled report.

## Many-leg slips (5+ legs)

A big accumulator must not print every leg every time — that is an unreadable wall on mobile. Instead:

- Keep the one-line header covering **all** legs, and add a `Progress:` counter line under it: `Progress: 4✅ 1🟢 8⏳ 0❌ 0❔` (LOST and DEAD both count under ❌; append `<count>⚪` only when a leg is VOID).
- Print leg lines **only** for legs that are live or settled. Pending legs exist only in the counts, acknowledged by one `Next up:` line.
- This requires the job prompt to hold the **full slip** (all legs), so the header counts and post-midnight confirmations are correct.

Example — a 13-leg World Cup slip, update at 18:30 (4 settled, one live):

```text
⚽️ Acca — 18:30 CEST · 🟡 PARTIAL · 4/13 settled
Progress: 4✅ 1🟢 8⏳ 0❌ 0❔
3) Spain 1-0 Cape Verde · 23' — Spain win: 🟢 WINNING
4) Sweden 2-1 Tunisia · FT — Sweden win: ✅ WON
Next up: Belgium vs Egypt KO 21:00
Next check: 18:45 CEST · ESPN
```

If a leg lost, the header flips (`❌ DEAD`) and that leg's line is shown; the rest continue as counts only, and later runs stay silent except final-settlement updates.
