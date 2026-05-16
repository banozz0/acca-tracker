# Example: Parsed Slip and Reports

## User request

> Track this acca: Arsenal vs PSG Arsenal win 1.55, Bayern vs Inter BTTS Yes 1.80, Luton vs Northampton Under 2.5 1.90.

## Parsed preview

```text
📋 Parsed acca — 3 legs

1. Arsenal vs PSG — Match result: Arsenal win — odds 1.55 — fields clear
2. Bayern vs Inter — BTTS: yes — odds 1.80 — fields clear
3. Luton vs Northampton — Total goals: under 2.5 — odds 1.90 — fields clear

Privacy: tracking jobs may store these match details until stopped or expired.

Start read-only tracking for this slip? Reply yes to create the job, or edit any leg first.
```

## Example report: compact live update

```text
⚽️ Acca update -- 22:15 CET
Overall: 🟡 LIVE / PARTIAL
Progress: 1✅ 1🟢 1⏳ 0❌ 0❔

1) Arsenal vs PSG
   Market: Arsenal win
   Score: FT 2-1
   Status: ✅ WON
   Source: Example official match centre

2) Bayern vs Inter
   Market: BTTS Yes
   Score: 1-1 HT
   Status: 🟢 WINNING
   Source: Example live-score source
   Next: final confirmation

3) Luton vs Northampton
   Market: Under 2.5 goals
   Score: not started
   Status: ⏳ PENDING
   Source: Example league fixture page
   Next: awaiting kickoff

Next check: 22:30 CET
Boundary: status only, no betting/cash-out advice.
```

## Regression: all legs unverifiable on first check continues

```text
⚽️ Acca update -- 16:30 GMT
Overall: ❔ UNVERIFIABLE
Progress: 0✅ 0🟢 0⏳ 0❌ 3❔

1) Arsenal vs PSG
   Market: Arsenal win
   Score: unavailable
   Status: ❔ UNVERIFIABLE
   Source: TheSportsDB/SofaScore/ESPN checked; no clear match
   Next: retry 16:45

2) Bayern vs Inter
   Market: BTTS Yes
   Score: unavailable
   Status: ❔ UNVERIFIABLE
   Source: BBC/SofaScore/search checked; ambiguous date
   Next: retry 16:45

3) Luton vs Northampton
   Market: Under 2.5 goals
   Score: unavailable
   Status: ❔ UNVERIFIABLE
   Source: league page/search checked; unreadable result
   Next: retry 16:45

Next check: 16:45 GMT
Boundary: status only, no betting/cash-out advice.
```

Rule asserted: this report does **not** include `TRACKING COMPLETE`; unverifiable lookup is non-terminal.

## Regression: one leg lost makes acca dead

```text
⚽️ Acca update -- 18:00 GMT
Overall: ❌ DEAD
Progress: 0✅ 0🟢 1⏳ 1❌ 0❔

1) Bayern vs Inter
   Market: BTTS Yes
   Score: FT 0-0
   Status: ❌ LOST
   Source: Example official match centre

2) Luton vs Northampton
   Market: Under 2.5 goals
   Score: not started
   Status: ⏳ PENDING
   Source: Example league fixture page
   Next: status only

Next check: 18:15 GMT
Boundary: status only, no betting/cash-out advice.
```

## Regression: user asks why no score

```text
I couldn't verify a score because the public sources checked were unavailable, unreadable, or did not clearly match the teams/date/competition. I won't guess a score. I'll keep the leg as UNVERIFIABLE and retry on the next scheduled check unless you stop tracking or provide clearer match details.
```

Recurring Telegram updates should be sent as the fenced `text` block itself, not as a loose paragraph. This keeps columns/indentation stable on mobile.

## Regression: live Bundesliga-style fixture lookup

```text
⚽️ Acca update -- 15:45 CET
Overall: 🟡 LIVE
Progress: 0✅ 1🟢 0⏳ 0❌ 0❔

1) Bayern Munich vs Dortmund
   Market: Over 2.5 goals
   Score: 2-1 68'
   Status: 🟢 WINNING
   Source: TheSportsDB + public match centre matched
   Next: final confirmation

Next check: 16:00 CET
Boundary: status only, no betting/cash-out advice.
```

Rule asserted: top-flight public fixtures should try TheSportsDB, SofaScore/search, ESPN/BBC-style sources, and official pages before `UNVERIFIABLE`.

## Regression: live Premier League-style fixture lookup

```text
⚽️ Acca update -- 16:10 GMT
Overall: 🟡 LIVE
Progress: 0✅ 1🟢 1⏳ 0❌ 0❔

1) Man United vs Chelsea
   Market: BTTS Yes
   Score: 1-1 HT
   Status: 🟢 WINNING
   Source: BBC Sport match page matched aliases/date
   Next: final confirmation

2) Liverpool vs Everton
   Market: Liverpool win
   Score: not started
   Status: ⏳ PENDING
   Source: official fixture page
   Next: kickoff 17:30

Next check: 16:25 GMT
Boundary: status only, no betting/cash-out advice.
```

Rule asserted: aliases such as `Man United` / `Manchester United` can be searched, while the original slip wording remains visible.

## Regression: mixed live/final legs

```text
⚽️ Acca update -- 19:30 GMT
Overall: 🟡 PARTIAL
Progress: 1✅ 1🟢 1⏳ 0❌ 0❔

1) Arsenal vs PSG
   Market: Arsenal win
   Score: FT 2-1
   Status: ✅ WON
   Source: official match centre

2) Bayern vs Inter
   Market: BTTS Yes
   Score: 1-1 52'
   Status: 🟢 WINNING
   Source: ESPN match centre
   Next: final confirmation

3) Luton vs Northampton
   Market: Under 2.5 goals
   Score: not started
   Status: ⏳ PENDING
   Source: competition fixture page
   Next: kickoff 20:00

Next check: 19:45 GMT
Boundary: status only, no betting/cash-out advice.
```

## Regression: ambiguous team names

```text
⚽️ Acca update -- 14:00 GMT
Overall: ❔ UNVERIFIABLE
Progress: 0✅ 0🟢 0⏳ 0❌ 1❔

1) Rangers vs United
   Market: Rangers win
   Score: unavailable
   Status: ❔ UNVERIFIABLE
   Source: TheSportsDB/SofaScore/search checked
   Next: retry 14:15

Note: multiple teams matched; need league/date confirmation.
Next check: 14:15 GMT
Boundary: status only, no betting/cash-out advice.
```

## Regression: unsupported market type

```text
⚽️ Acca update -- 14:00 GMT
Overall: ❔ UNVERIFIABLE
Progress: 0✅ 0🟢 0⏳ 0❌ 1❔

1) Arsenal vs Chelsea
   Market: Player shots on target
   Score: live score found; prop data unavailable
   Status: ❔ UNVERIFIABLE
   Source: BBC/SofaScore public score checked
   Next: retry 14:15

Note: market needs player-prop data not in basic public scores.
Next check: 14:15 GMT
Boundary: status only, no betting/cash-out advice.
```
