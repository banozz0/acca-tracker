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

## Example report: mixed live/pending/finished

```text
🏟️ Acca status — 22:15 CET

Overall: ALIVE

1. Arsenal vs PSG — FT 2-1 — Arsenal win — WON
   Source: Example official match centre
   Confidence: high
   Note: Final score satisfies the leg.

2. Bayern vs Inter — 1-1, HT — BTTS yes — WINNING
   Source: Example live-score source
   Confidence: medium
   Note: Both teams have scored; final confirmation still pending.

3. Luton vs Northampton — not started — Under 2.5 goals — PENDING
   Source: Example league fixture page
   Confidence: medium
   Note: Kickoff is later; no score yet.

Summary: 1 won / 1 winning / 1 pending / 0 lost / 0 dead / 0 void / 0 unverifiable.
Next: next scheduled check if tracking is active.
Boundary: status tracking only; not betting or cash-out advice.
```

## Example report: lost leg

```text
Overall: DEAD

1. Bayern vs Inter — FT 0-0 — BTTS yes — LOST
   Source: Example official match centre
   Confidence: high
   Note: Both teams did not score, so this leg failed.

Summary: acca is dead because at least one leg lost. Remaining legs can still be reported for status only.
```

## Example report: unavailable data

```text
Overall: UNVERIFIABLE

1. Town FC vs United FC — score unavailable — Match result: Town FC win — UNVERIFIABLE
   Source: checked public search results; no reliable matching fixture found
   Confidence: unverifiable
   Note: Team names are ambiguous and the kickoff date is missing. Ask the user to confirm league/date or provide a clearer slip.
```
