# Compact Report Format

Use this format for recurring scheduled Telegram/mobile updates. Send the whole update as a single fenced `text` codeblock so Telegram keeps the compact tracker alignment on mobile.

```text
⚽️ Acca update -- 16:30
Overall: 🟡 LIVE / PARTIAL / UNVERIFIABLE
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
Overall: <emoji> <status>
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
- Use sparse emojis: ✅ won, 🟢 live/winning, ⏳ pending, ❌ lost/dead, ❔ unverifiable, ⚪ void.
- Include `Next check` whenever tracking continues.
- Make next timing clear: `Next: retry 16:45`, `Next: kickoff 20:00`, `Next: final`, or `Next: status only`.
- Keep most lines under about 72 characters.
- Use `TRACKING COMPLETE` only when every leg is final/settled, the max check count is reached, or the user stopped tracking.
- Do not include betting advice, predictions, cash-out advice, or odds optimization.
