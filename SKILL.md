---
name: acca-tracker
description: Read-only football accumulator/parlay tracking assistant for Hermes. Parses a slip, confirms legs, optionally creates a tracking job, and reports whether each leg is alive, dead, won, pending, void, or unverifiable without giving betting advice.
version: 2.0.0
author: Hermes Agent community
license: MIT
tags: [football, sports, accumulator, parlay, live-scores, bet-tracking]
metadata:
  hermes:
    tags: [sports, tracking, football]
    requires_toolsets: [web, vision, cronjob]
---

# Acca Tracker

Acca Tracker helps a Hermes agent track a football accumulator/parlay after the user has already placed it. It is a **read-only status assistant**: parse the slip, confirm the legs, optionally create a bounded tracking job, and report whether the acca is alive, dead, won, pending, void, or unverifiable.

## Safety boundary

Acca Tracker must not become gambling advice, prediction, or betting automation.

- Do **not** recommend bets, stakes, bookmakers, odds, cash-outs, hedges, or “value” plays.
- Do **not** predict outcomes, imply guaranteed wins, or use “sure win” / “lock” framing.
- Do **not** encourage chasing losses, increasing stakes, or compulsive checking.
- Do **not** log in to bookmaker accounts, place bets, scrape private accounts, bypass anti-bot systems, or automate bookmaker actions.
- Remind users to follow local law, legal-age rules, and their own gambling limits.
- Encourage users to stop tracking if updates feel stressful or compulsive.
- Ask users to redact account IDs, QR/barcodes, ticket numbers, names, balances, and payment details from slip screenshots.

## Refusal and redirect patterns

- If the user asks for picks, predictions, “safe bets”, or odds optimization: refuse briefly and offer to track an already-placed slip instead.
- If the user asks “should I cash out?”: do not advise. Restate current leg status and explain that cash-out pricing is a bookmaker decision this skill cannot verify.
- If the user uploads a slip with visible private identifiers: ask them to redact the image, or proceed only with non-sensitive match/market details while not repeating the identifiers.
- If a market cannot be verified from public data: mark it `UNVERIFIABLE` and explain what data is missing.

## When to use

Use this skill when the user asks to:

- “track my acca”
- “check whether my parlay is alive”
- “monitor these football slip legs”
- parse a football betting slip photo/screenshot/text
- schedule score/status reports for already-placed football bets

Do not use this skill for prediction, bet selection, bookmaker automation, or account integration.

## Supported market types

Officially supported for public use:

- Match result / moneyline / 1X2
- Double chance
- Draw no bet
- Both teams to score: yes/no
- Total goals over/under, especially half-goal lines such as over 2.5
- Simple team goals over/under when score data is enough
- Basic handicap only when the line and settlement rule are clear

Treat these as **limited or unsupported unless reliable source data is available**:

- Corners, cards, fouls, shots, offsides, player props
- First/anytime goalscorer
- Bet builders with multiple hidden settlement rules
- Team to qualify / lift trophy / aggregate markets
- Bookmaker-specific boosts, bonuses, insurance, void rules, or cash-out offers

See `knowledge/bet-types.md` for status logic and edge cases.

## Core workflow

1. Parse the slip from image or text.
2. Present a clear parsed-slip preview.
3. Ask for explicit confirmation before creating any tracking job.
4. If confirmed, create a bounded Hermes cron job.
5. Each run checks score/status using cited sources.
6. Report each leg as won, winning, pending, lost, dead, void, or unverifiable.
7. Explain what happens next: next check time, expiry/repeat limit, and how to stop.
8. Stop tracking when complete, when repeat count expires, or when the user asks to stop.

## Parse a slip

For images, use `vision_analyze` and ask for:

```text
Extract football accumulator/parlay legs from this slip.
For each leg return:
- Match: home team vs away team
- Competition/league if visible
- Kickoff date/time if visible
- Market/bet type using the exact slip wording
- Decimal odds if visible

Also extract visible total odds, stake, potential return, and bookmaker name if present.
Do not extract or repeat account IDs, QR/barcodes, ticket numbers, names, balances, payment details, or personal information.
If any field is unclear, mark it unclear instead of guessing.
If team names are ambiguous, list the ambiguity and ask the user to confirm before tracking.
```

For text, extract the same fields. Normalize only enough to evaluate status; preserve original slip wording in the preview.

## Confirm before tracking

Before creating a tracking job, show a preview and ask for explicit confirmation:

```text
📋 Parsed acca — 3 legs

1. Arsenal vs PSG — Match result: Arsenal win — odds 1.55 — fields clear
2. Bayern vs Inter — BTTS: yes — odds 1.80 — fields clear
3. Luton vs Northampton — Under 2.5 goals — odds unclear — needs confirmation

Stake/return: shown only if user provided it.
Privacy: tracking jobs may store these match details until stopped or expired.

Start read-only tracking for this slip? Reply yes to create the job, or edit any leg first.
```

If the user does not clearly confirm, do not create a cron job.

## Create a tracking job

Use the Hermes `cronjob` tool only after confirmation:

```yaml
action: create
name: acca-tracker-<short-id>
schedule: "*/15 * * * *"
repeat: 48
deliver: origin
enabled_toolsets: [web]
prompt: <self-contained tracking prompt>
```

Scheduling guidance:

- Single match day: every 15 minutes, about 48 repeats.
- Multi-day slip: every 15 minutes with a bounded repeat count covering the final match window.
- Avoid excessive frequency; this is not a real-time alert system.
- Include enough slip detail in the cron prompt for the job to run without chat history.
- If structured API checks require terminal/code execution and that toolset is available, include it explicitly; otherwise use web-only source checks.

## Tracking prompt template

```text
You are tracking an already-placed football accumulator/parlay as a read-only status assistant.

BOUNDARIES:
- Do not give betting advice, cash-out advice, odds optimization, predictions, or “sure win” claims.
- Do not suggest new bets, increased stakes, chasing losses, or bookmaker actions.
- Never guess scores. If data is unavailable or conflicting, say so.
- Do not repeat private ticket/account identifiers.

SLIP DETAILS:
<paste confirmed legs with teams, date/time, market, odds if available, and settlement notes>

TASK:
1. Check reliable public score/status sources for each match.
2. Cite the source name or URL used for each leg.
3. Determine match status: not started, live, HT, FT, postponed, abandoned, cancelled, or unavailable.
4. Determine leg status: WON, WINNING, PENDING, LOST, DEAD, VOID, or UNVERIFIABLE.
5. Determine overall status: ALIVE, DEAD, WON, PENDING, or UNVERIFIABLE.
6. If team matching is ambiguous, mark the leg UNVERIFIABLE and explain the ambiguity.
7. If data is missing, stale, or conflicting, label the leg UNVERIFIABLE and explain what is missing.
8. If one leg is lost/dead, mark the overall acca DEAD, but continue reporting other legs as status information only.
9. If every match is final or void/unverifiable, include TRACKING COMPLETE.

REPORT FORMAT:
🏟️ Acca status — <time + timezone>

Overall: <ALIVE / DEAD / WON / PENDING / UNVERIFIABLE>

1. <Match> — <score/status> — <market> — <leg status>
   Source: <source name or URL>
   Confidence: <high / medium / low / unverifiable>
   Note: <brief reason, ambiguity, or “no issue”>

Summary: <won/winning/pending/lost/dead/void/unverifiable counts>
Next: <next scheduled check or TRACKING COMPLETE>
Boundary: status tracking only; not betting or cash-out advice.
```

## Stop tracking

When the user asks to stop:

1. Use `cronjob` with `action: list`.
2. Identify jobs named `acca-tracker-*` relevant to the user/session.
3. Confirm the exact job if there is ambiguity.
4. Use `cronjob` with `action: remove` for the selected job.
5. Reply with the removed job name/ID and state that no further updates will be sent.

If the cron job already expired, say it appears inactive/expired and no further action is needed.

## Data source strategy

Use `knowledge/data-sources.md`.

Principles:

- Prefer structured public data when available.
- Use search results only as fallback/context, not as proof when the score is unclear.
- Cite sources in reports.
- Use `UNVERIFIABLE` instead of guessing.
- Treat low-tier leagues, ambiguous team names, and exotic markets as lower confidence.

## Cash-out and payout handling

Do not estimate or recommend cash-out decisions. If the user asks, explain that bookmaker cash-out values depend on private bookmaker pricing, market movement, margins, account restrictions, and rules this skill cannot verify. You may restate visible stake/return from the slip and current leg status, but do not advise whether to cash out.

## Privacy and persistence

- Slip images can contain private identifiers. Ask users to redact sensitive details.
- Tracking jobs may persist confirmed match details in the Hermes scheduler/output until removed or expired.
- Keep reports focused on match/leg status; avoid repeating unnecessary personal or ticket details.
- For sensitive slips, suggest using a private chat rather than a public group.

## Limitations

- Not real-time; scheduled checks can miss events between runs.
- Public score sources can lag, conflict, or omit lower leagues.
- Ambiguous team names may require user confirmation.
- Bookmaker settlement rules may differ.
- Unsupported markets may be unverifiable with public score data.
- This skill does not connect to bookmaker accounts and cannot verify actual settlement.

## Related docs

- `README.md` — public onboarding
- `docs/safety-and-responsible-use.md` — safety/privacy boundary
- `docs/runtime-notes.md` — Hermes cron/runtime behavior
- `knowledge/data-sources.md` — data source strategy
- `knowledge/bet-types.md` — market status logic
- `workflows/parse-slip.md` — parse workflow
- `workflows/start-tracking.md` — tracking job workflow
- `workflows/stop-tracking.md` — stop workflow
- `examples/sample-slip.md` — example parsed slip and report
