# Compact Report Format

Use this format for recurring scheduled Telegram/mobile updates. Send the whole update as a single fenced `text` codeblock so Telegram keeps the compact tracker alignment on mobile.

```text
⚽️ Acca update -- 16:30 GMT
Overall: ❔ UNVERIFIABLE — 0/5 settled, 0 lost
Progress: 0✅ 0🟢 0⏳ 0❌ 5❔

1) Chelsea vs Man City
   Market: Man City win + BTTS Yes
   Score: unavailable
   Status: ❔ UNVERIFIABLE
   Source: ESPN/BBC/SofaScore checked
   Next: retry 16:45

Next check: 16:45
Boundary: status only, no betting/cash-out advice.
```

Before v2.0.2, reports could render as normal markdown paragraphs. In v2.0.2, recurring tracker updates should render as compact terminal-style text blocks:

````text
```text
⚽️ Acca update -- <HH:MM timezone>
Overall: <emoji> <status> — <settled>/<total> settled, <lost> lost
Progress: <count>✅ <count>🟢 <count>⏳ <count>❌ <count>❔

1) <Match>
   Market: <short market>
   Score: <score/status or unavailable>
   Status: <emoji> <leg status>
   Source: <source used or compact checked list>
   Next: <retry/kickoff/final/status only>

Next check: <HH:MM timezone>
Boundary: status only, no betting/cash-out advice.
```
````

Rules:

- Use at most 4-5 short lines per leg.
- Cite the source used or the sources checked for each leg.
- Put caveats once at the bottom.
- Keep caveats short, for example: `Note: source dates conflicted; retrying.`
- Leg-status emojis: ✅ won, 🟢 live/winning, ⏳ pending, ❌ lost/dead, ❔ unverifiable, ⚪ void.
- Overall-status emojis: ✅ WON, 🟢 LIVE, 🟡 PARTIAL, ⏳ PENDING, ❌ DEAD, ❔ UNVERIFIABLE.
- Progress counters use leg-status emojis ✅ 🟢 ⏳ ❌ ❔ (LOST and DEAD both count under ❌). Append a `<count>⚪` only when at least one leg is VOID.
- Include `Next check` whenever tracking continues.
- Make next timing clear: `Next: retry 16:45`, `Next: kickoff 20:00`, `Next: final`, or `Next: status only`.
- Keep most lines under about 72 characters.
- Use `TRACKING COMPLETE` only when every leg is final/settled, Hermes explicitly says the max-repeat run has been reached, or the user stopped tracking.
- Do not include betting advice, predictions, cash-out advice, or odds optimization.

## Many-leg slips (summary + active detail)

A big accumulator (5+ legs, often across several dates) must not print every leg in full every 15 minutes — that is an unreadable wall of "not started" on mobile. Instead:

- **Stay silent when nothing is happening.** Before any leg is live, and on any run where nothing is live or newly settled, respond with the runtime's silent token (`[SILENT]` in Hermes) instead of sending a "nothing yet" update. Otherwise the job spams a message every interval.
- Keep the `Overall` + `Progress` header covering **all** legs, so the whole-acca standing is always visible.
- Print a per-leg block **only** for legs that are live (WINNING) or settled (WON/LOST/DEAD/VOID). **Never print a PENDING / not-started leg as its own block** — they exist only as the ⏳ count.
- If you are sending but no leg is live or settled yet, use a single line such as `No legs live or settled yet.` plus a `Next up:` line — no leg blocks.
- Add a short `Next up` line and an `N legs still to play` count so upcoming legs are acknowledged without detail.
- Output only the report itself — never echo instruction markers (`‼️`), prompt headings, or meta-notes.
- This requires the job prompt to hold the **full slip** (all legs), so the header counts and any post-midnight confirmations are correct.

Example — a 13-leg World Cup slip, update on 15 June at 18:30 (4 legs already settled, one live, the rest upcoming):

```text
⚽️ Acca update -- 18:30 CEST
Overall: 🟡 PARTIAL — 4/13 settled, 0 lost
Progress: 4✅ 1🟢 8⏳ 0❌ 0❔

Live now:
3) Spain vs Cape Verde
   Market: Spain win
   Score: 1-0 23'
   Status: 🟢 WINNING · Source: ESPN

Settled today:
4) Sweden vs Tunisia — Sweden win — FT 2-1 — ✅ WON

Next up today: 5) Belgium vs Egypt 21:00
Next check: 18:45 CEST · 8 legs still to play
Boundary: status only, no betting/cash-out advice.
```

If a leg lost, the header flips (`Overall: ❌ DEAD — acca lost on leg N`) and that leg is detailed; the rest continue as status-only counts.
