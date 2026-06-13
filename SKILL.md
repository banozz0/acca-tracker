---
name: acca-tracker
description: "Use when tracking an already-placed football accumulator/parlay: parse a slip, confirm legs, create bounded read-only cron status checks, and report public match status without betting advice."
version: 2.1.0
author: Hermes Agent community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sports, football, accumulator, parlay, live-scores, bet-tracking]
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
- If the user says or implies they are under legal gambling age, or that gambling is illegal for them/their location, do not help track betting activity. Offer general responsible-use/support guidance instead.
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
6. Report each leg as won, winning, pending, lost, dead, void, or unverifiable. Treat unverifiable/data-unavailable states as retryable, not terminal.
7. Explain what happens next: next check time, expiry/repeat limit, and how to stop.
8. Stop tracking only when every leg is final/settled, when Hermes explicitly says the max-repeat run has been reached, or when the user asks to stop. Lookup failure alone must not complete tracking.

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

Only extract stake, potential return, total odds, or bookmaker name if the user explicitly asks or if needed for a one-time preview. Do not include those fields in scheduled tracking prompts unless the user explicitly requests it.
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
schedule: "*/15 20-23 * * *"   # poll only during the match-night window
repeat: 48                      # = firings-per-window × number of match nights
deliver: origin
enabled_toolsets: [web]
prompt: <self-contained tracking prompt>
```

Scheduling guidance — window the cron to the actual match times; do not poll 24/7. Hermes accepts full cron expressions and `repeat` counts firings, so:

- Derive the kickoff dates/times from the parsed slip first.
- Restrict the **hours** to the match window: for a 21:00 kickoff use `20-23` (covers lead-in + 90 min + halftime + stoppage + settlement). Widen only if kickoffs span more hours.
- Multi-day slip with games clustered at the same time: one windowed job is enough — `*/15 20-23 * * *` stays silent through the 20+ hour gaps between match nights automatically.
- If the exact match dates are known, target them: `*/15 20-23 13,15,18 6 *` fires only those evenings (June 13/15/18) and skips non-match days entirely.
- Size `repeat` to cover through the **last** match night: `firings_per_window × match_nights` plus a small buffer (a 4-hour window ≈ 16 firings/night, so 3 nights ≈ 48).
- If kickoff times differ a lot across days, widen the window or create one job per match-night cluster (each auto-expires when its repeat budget ends).
- Never emit `*/15 * * * *` for a multi-day slip — it polls dead hours and burns the repeat budget before later games start.
- Include enough slip detail in the cron prompt for the job to run without chat history.
- If structured API checks require terminal/code execution and that toolset is available, include it explicitly; otherwise use web-only source checks.

### Varied kickoff times across dates

When a slip's legs span multiple dates with kickoffs at different hours (common for World Cup / multi-competition slips), do not force one tight window and do not poll 24/7. Group the legs by date and create **one windowed cron job per match date**:

1. Group the confirmed legs by kickoff date.
2. For each date, take that date's earliest and latest kickoff hour. The window runs from the earliest kickoff hour to the latest kickoff hour + ~3 (covers 90 min + halftime + stoppage + settlement).
3. Emit `*/15 <hours> <day> <month> *`, date-targeted so it fires only on that date. Skip dates with no legs entirely — no job, no checks.
4. Spillover: a 22:00+ kickoff finishes after midnight, so also fire the early hours of the next day (add `0,1` on the following date) to confirm the final whistle, or accept that the leg settles on the next date's job. State which you chose.
5. Size each job's `repeat` to its own window (~4 firings/hour × window hours) plus a small buffer.
6. Name jobs distinctly per date, e.g. `acca-tracker-<short-id>-<MMDD>`, so the stop-tracking flow can list and remove them all (`acca-tracker-*`).
7. **Every per-date job's prompt must contain the full confirmed slip (all legs), not just that date's legs.** Each run needs the whole slip to compute the overall acca status across all legs and to confirm a prior night's late game that finishes after midnight (spillover). The kickoff-time efficiency rule still applies: report not-yet-started legs as PENDING without querying them.

Example — a slip with games on 14, 15 (04:00/18:00/21:00), 16, 18, 20, 23 June:

| Date | Cron | Notes |
| --- | --- | --- |
| 14 Jun | `*/15 22,23 14 6 *` | + `*/15 0,1 15 6 *` to confirm the post-midnight final |
| 15 Jun | `*/15 4,5,6,18-23 15 6 *` | early + evening kickoffs same day |
| 16 Jun | `*/15 21,22,23 16 6 *` | |
| 18 Jun | `*/15 19-23 18 6 *` | |
| 20 Jun | `*/15 19-23 20 6 *` | |
| 23 Jun | `*/15 19-23 23 6 *` | |

Dates with no legs (e.g. 19, 21, 22 June) get no job and zero checks.

Simpler single-job alternative (more wasted runs): one union schedule across all match dates, e.g. `*/15 0,3-6,18-23 14,15,16,17,18,20,23 6 *`. Prefer per-date jobs when minimizing scheduled runs matters.

**Timezone:** the cron hours, the slip's printed kickoff times, and the Hermes scheduler must share one timezone. Confirm the slip's timezone with the user (or normalize to the scheduler's timezone) before emitting the schedule — a mismatch shifts every window and can miss kickoffs. State the timezone used in the confirmation preview.

## Tracking prompt template

````text
You are tracking an already-placed football accumulator/parlay as a read-only status assistant.

BOUNDARIES:
- Do not give betting advice, cash-out advice, odds optimization, predictions, or “sure win” claims.
- Do not suggest new bets, increased stakes, chasing losses, or bookmaker actions.
- Never guess scores. If data is unavailable or conflicting, say so.
- Do not repeat private ticket/account identifiers.
- If the interaction reveals the user is underage or gambling is illegal for them, stop status tracking and advise them not to use betting-tracking assistance.

SLIP DETAILS:
<paste confirmed legs with teams, competition/date/time, market wording, and settlement notes. Do not include stake, return, ticket/account identifiers, balances, QR/barcodes, or payment details. Omit odds unless the user explicitly requested them for display.>

TASK:
1. Normalize team names before searching: remove FC/AFC/CF/SC suffix noise, expand common abbreviations only when obvious, preserve original names in the report, and keep aliases paired with competition/date.
2. Build 3-5 targeted queries per leg before giving up:
   - "<home> <away> live score <date> <competition>"
   - "<home> vs <away> result <date>"
   - "<home> <away> SofaScore <date>"
   - "<home> <away> ESPN BBC <competition>"
   - "<competition/team official> <home> <away> match centre"
3. Check reliable public score/status sources in this ladder:
   a. ESPN scoreboard API (primary): https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates=YYYYMMDD (or /all/ for every competition). Read status.type.state (pre/in/post), status.type.description, status.displayClock (live minute), and competitors[].score. This is the main source for live in-play status.
   b. TheSportsDB eventsday (https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=YYYY-MM-DD&s=Soccer) as a secondary structured cross-check for final scores; its free tier has no live endpoint and capped coverage.
   c. ESPN/BBC/Sky/TNT/Guardian reputable match-centre web pages when the API is missing a fixture.
   d. Official competition/team pages.
   e. SofaScore or general web-search snippets as context only (SofaScore direct fetch is usually bot-blocked); not sole proof when unclear.
4. Match by both teams, competition/league, date/kickoff window, and home/away orientation when relevant. If a source matches only one team or a different date/competition, keep searching.
5. Cite the source name or URL used for each leg; for failures, cite the compact source group checked.
6. Determine match status: not started, live, HT, FT, postponed, abandoned, cancelled, or unavailable.
7. Determine leg status: WON, WINNING, PENDING, LOST, DEAD, VOID, or UNVERIFIABLE.
8. Determine overall status: LIVE, PARTIAL, DEAD, WON, PENDING, or UNVERIFIABLE.
9. If team matching is ambiguous, mark the leg UNVERIFIABLE and explain the ambiguity in one short phrase.
10. If data is missing, stale, or conflicting after the source ladder, label the leg UNVERIFIABLE and briefly state the mismatch/failure. UNVERIFIABLE, DATA_UNAVAILABLE, and UNKNOWN are non-terminal states.
11. If one leg is lost/dead, mark the overall acca DEAD, but continue reporting other legs as status information only.
12. Include TRACKING COMPLETE only when every leg is terminal/settled, or when the scheduler/runtime explicitly says this is the final/max-repeat run. Never complete tracking because lookup failed, sources were blocked, all legs were unverifiable, or you merely believe the repeat window should be over.

EFFICIENCY (multi-day slips):
- Each run, compare every leg's kickoff to the current time. Legs whose kickoff is still in the future have not started — report them PENDING without searching for a score. Only fetch legs that are in-play or already finished.
- This avoids pointless lookups for later match nights while the current night's games are live.

REPORT FORMAT (compact Telegram/mobile):
Return recurring tracker updates as one compact fenced text block. Put only the codeblock in the scheduled update unless a safety refusal is needed outside it.

```text
⚽️ Acca update -- <HH:MM timezone>
Overall: <emoji> <WON|LIVE|PARTIAL|PENDING|DEAD|UNVERIFIABLE>
Progress: <count>✅ <count>🟢 <count>⏳ <count>❌ <count>❔

1) <Match>
   Market: <short market wording>
   Score: <score + match clock/status, or unavailable>
   Status: <emoji> <WON / WINNING / PENDING / LOST / DEAD / VOID / UNVERIFIABLE>
   Source: <source name or URL, or sources checked>
   Next: <retry HH:MM / kickoff HH:MM / final / status only>

Note: <only if needed: one short source mismatch/failure caveat>

Next check: <HH:MM timezone>
Boundary: status only, no betting/cash-out advice.
```

Formatting rules:
- Keep each leg to at most 4-5 short lines.
- Put caveats once at the bottom, not repeated in every leg.
- Leg-status emojis: ✅ won, 🟢 currently winning/live, ⏳ pending, ❌ lost/dead, ❔ unverifiable, ⚪ void.
- Overall-status emojis: ✅ WON, 🟢 LIVE, 🟡 PARTIAL, ⏳ PENDING, ❌ DEAD, ❔ UNVERIFIABLE.
- Progress counters use leg-status emojis ✅ 🟢 ⏳ ❌ ❔ (LOST and DEAD both count under ❌). Append a `<count>⚪` only when at least one leg is VOID.
- Many-leg slips (5+ legs): keep the `Overall` + `Progress` header covering **all** legs, but give full per-leg detail only for legs that are **live or settled in the current window**. Roll already-settled and not-yet-started legs into the Progress counts instead of listing them in full every run, and add a short `Next up` / `N legs still to play` line. See `docs/compact-report-format.md`.
- Include a source/citation for each leg.
- Include Next check when continuing and make the next retry time explicit.
- Keep most lines under ~72 characters for mobile scanning.
- Preserve source lines and the next-check line inside the fenced text block.
- Use TRACKING COMPLETE only when terminal conditions are actually met.
````

## Updating active tracking jobs after skill fixes

Skill edits do not automatically change cron jobs that were already created with an older prompt. If a live tracker exposed a behavior bug and the skill is patched, update or recreate the active `acca-tracker-*` job prompt in the same session when the user expects the current tracker to improve immediately.

When updating a live job:

1. Keep the existing schedule, repeat budget, delivery target, and confirmed slip details unless the user asks otherwise.
2. Patch only the self-contained tracking prompt to include the corrected status logic, source policy, and compact format.
3. Verify the job remains enabled and report the next run time.
4. Do not touch unrelated scheduler jobs or account/bookmaker integrations.

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
- Source priority: ESPN scoreboard API (live in-play + final scores) first; TheSportsDB eventsday as a secondary structured cross-check for final scores (free tier has no live endpoint); ESPN/BBC/Sky/TNT/Guardian match-centre pages; official league/team pages; then web-search snippets and `UNVERIFIABLE` while continuing to track.
- SofaScore direct fetches are usually bot-blocked (HTTP 403); use SofaScore only via web-search snippets, never as a primary fetch target, and never describe it as an official public API. If a source is blocked, unreadable, or ambiguous, mark it unavailable and continue.
- Do not stop after one failed source. Retry with normalized team names, aliases, competition/date terms, and official-source phrasing before marking a legitimate public fixture `UNVERIFIABLE`.

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
- `docs/compact-report-format.md` — compact Telegram/mobile reporting format
- `knowledge/data-sources.md` — data source strategy
- `knowledge/bet-types.md` — market status logic
- `workflows/parse-slip.md` — parse workflow
- `workflows/start-tracking.md` — tracking job workflow
- `workflows/stop-tracking.md` — stop workflow
- `examples/sample-slip.md` — example parsed slip and report
- `references/profile-install-and-hardening.md` — profile-safe install, hardening checklist, and validation probe
