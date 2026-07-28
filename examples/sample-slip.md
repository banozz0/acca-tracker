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
Reports are status-only — no betting or cash-out advice.

Start read-only tracking for this slip? Reply yes to create the job, or edit any leg first.
```

The boundary line appears here once; recurring updates do not repeat it.

## Example report: compact live update

```text
⚽️ Acca — 22:15 CET · 🟡 PARTIAL · 1/3 settled
1) Arsenal 2-1 PSG · FT — Arsenal win: ✅ WON
2) Bayern 1-1 Inter · HT — BTTS Yes: 🟢 WINNING
3) Luton 0-0 Northampton · KO 22:30 — Under 2.5: ⏳ PENDING
Next check: 22:30 CET · ESPN
```

## Regression: unchanged scores stay silent

If the script prints `CHANGE SINCE LAST RUN: NO`, the run responds `[SILENT]` — no message is sent, even while matches are live. The match clock moving is not a change.

## Regression: all legs unverifiable on first check continues

```text
⚽️ Acca — 16:30 GMT · ❔ UNVERIFIABLE · 0/3 settled
1) Arsenal vs PSG — Arsenal win: ❔ UNVERIFIABLE
2) Bayern vs Inter — BTTS Yes: ❔ UNVERIFIABLE
3) Luton vs Northampton — Under 2.5: ❔ UNVERIFIABLE
Note: ESPN API/TheSportsDB/search checked; no clear match. Retrying.
Next check: 16:45 GMT · ESPN
```

Rule asserted: this report does **not** include `TRACKING COMPLETE`; unverifiable lookup is non-terminal.

## Regression: one leg lost makes acca dead

```text
⚽️ Acca — 18:00 GMT · ❌ DEAD · 1/2 settled
1) Bayern 0-0 Inter · FT — BTTS Yes: ❌ LOST
2) Luton 0-0 Northampton · KO 20:00 — Under 2.5: ⏳ PENDING
Next check: 18:15 GMT · ESPN
```

After this death notice, later runs stay `[SILENT]` until the remaining leg reaches its final result.

## Regression: user asks why no score

```text
I couldn't verify a score because the public sources checked were unavailable, unreadable, or did not clearly match the teams/date/competition. I won't guess a score. I'll keep the leg as UNVERIFIABLE and retry on the next scheduled check unless you stop tracking or provide clearer match details.
```

## Regression: alias lookup

```text
⚽️ Acca — 16:10 GMT · 🟢 LIVE · 0/2 settled
1) Man United 1-1 Chelsea · HT — BTTS Yes: 🟢 WINNING
2) Liverpool 0-0 Everton · KO 17:30 — Liverpool win: ⏳ PENDING
Next check: 16:25 GMT · ESPN
```

Rule asserted: aliases such as `Man United` / `Manchester United` can be matched, while the original slip wording remains visible. Top-flight fixtures should try the ESPN scoreboard API first, then TheSportsDB, match-centre pages, official pages, and search snippets before `UNVERIFIABLE`.

## Regression: ambiguous team names

```text
⚽️ Acca — 14:00 GMT · ❔ UNVERIFIABLE · 0/1 settled
1) Rangers vs United — Rangers win: ❔ UNVERIFIABLE
Note: multiple teams matched; need league/date confirmation.
Next check: 14:15 GMT · ESPN
```

## Regression: void leg counts and keeps acca alive

```text
⚽️ Acca — 21:00 GMT · 🟡 PARTIAL · 2/3 settled
1) Arsenal 1-1 PSG · FT — DNB Arsenal: ⚪ VOID
2) Bayern 2-1 Inter · FT — BTTS Yes: ✅ WON
3) Luton 0-0 Northampton · KO 21:30 — Under 2.5: ⏳ PENDING
Next check: 21:15 GMT · ESPN
```

Rule asserted: a void (not lost) leg keeps the acca PARTIAL rather than DEAD.

## Regression: unsupported market type

```text
⚽️ Acca — 14:00 GMT · ❔ UNVERIFIABLE · 0/1 settled
1) Arsenal vs Chelsea — Player shots on target: ❔ UNVERIFIABLE
Note: market needs player-prop data not in basic public scores.
Next check: 14:15 GMT · ESPN
```

## Regression: fallback source cited on the leg line

```text
⚽️ Acca — 15:45 CET · 🟢 LIVE · 0/1 settled
1) Bayern 2-1 Dortmund · 68' — Over 2.5: 🟢 WINNING (via BBC)
Next check: 16:00 CET · ESPN
```

Recurring Telegram updates are sent as the fenced `text` block itself, not as a loose paragraph, with no boundary footer.
