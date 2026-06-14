# Runtime Notes

Acca Tracker is designed for Hermes sessions with optional scheduled jobs.

## Confirmation before persistence

Creating a cron job persists a self-contained tracking prompt with confirmed match details. Always preview the parsed slip and ask the user to explicitly confirm before creating the job.

Tell the user what happens next:

- job name
- check interval
- approximate expiry/repeat count
- how to stop tracking
- that confirmed match details may be persisted until the job expires or is removed

## Suggested cron settings

Window the schedule to the match times instead of polling 24/7. Hermes accepts full cron expressions and `repeat` counts firings.

```yaml
action: create
name: acca-tracker-<short-id>
schedule: "*/15 20-23 * * *"   # match-night window only; 21:00 kickoffs
repeat: 48                      # firings-per-window × number of match nights
deliver: origin
enabled_toolsets: [web]
```

- Restrict hours to the kickoff window (`20-23` for a 21:00 KO). The job then stays silent through the long gaps between match nights.
- If exact match dates are known, target them: `*/15 20-23 13,15,18 6 *` fires only those evenings.
- Size `repeat` to reach the last match night (~16 firings per 4-hour window per night).
- Never use `*/15 * * * *` for a multi-day slip: it polls dead hours and exhausts the repeat budget before later games start.
- When kickoff times vary a lot across dates, create one windowed job per match date (`acca-tracker-<short-id>-<MMDD>`) instead of one schedule; handle post-midnight finals by adding the next day's early hours, and keep cron hours, slip times, and the scheduler in one timezone. See "Varied kickoff times across dates" in SKILL.md.
- Add other toolsets only when the running Hermes environment supports them and the job genuinely needs them.

## Stopping a tracker

Use `cronjob` list/remove flow:

1. List jobs.
2. Find relevant `acca-tracker-*` jobs.
3. Confirm if ambiguous.
4. Remove the selected job.
5. Tell the user updates have stopped.

## Data unavailable behavior

When score/status data is missing, stale, ambiguous, or conflicting:

- mark the leg `UNVERIFIABLE`
- cite what was checked
- do not guess scores
- try normalized team aliases plus competition/date search before giving up
- try TheSportsDB, readable SofaScore/public pages, ESPN/BBC-style match centres, official pages, and fallback search where appropriate
- do not infer final results from kickoff time alone
- ask for clarification when team names or kickoff dates do not uniquely identify the match
- keep the source mismatch/failure note brief and avoid repeating the same caveat per leg


## Terminal-state rules

`UNVERIFIABLE`, `DATA_UNAVAILABLE`, and `UNKNOWN` are **non-terminal**. They mean the current check could not verify the leg, not that the tracker is finished. Continue scheduled tracking until one of these happens:

- all legs are final/settled (`WON`, `LOST`, `DEAD`, `VOID`, or otherwise explicitly settled),
- Hermes explicitly says the bounded max-check/repeat count is reached, or
- the user stops the tracker.

Never say `TRACKING COMPLETE` only because public lookup failed, a source was blocked, all legs were unverifiable on a check, or wall-clock time suggests the repeat window should be over. In those cases, include `Next check` and retry later.

## Time awareness (scheduled runs are time-blind)

Hermes does not inject the current time into a cron agent's prompt — the agent cannot tell what time it is unless you give it to it. If a tracking prompt asks the agent to decide "future vs started" from its own clock, it will hallucinate a timestamp and skip every leg as "future, not searched," so the tracker never actually checks scores.

Avoid this two ways:

- **Status from the source, not the clock.** Bake `RUN DATE: <YYYY-MM-DD>` into each per-date job and have it query the ESPN scoreboard for that date every run; the API's `status.type.state` (`pre`/`in`/`post`) decides not-started/live/finished. Legs on later dates stay PENDING.
- **Real time for the header.** Attach a tiny script that prints the current time and is injected into the prompt each run: `~/.hermes/scripts/now.sh` → `date '+CURRENT TIME: %Y-%m-%d %H:%M:%S %Z'`, created with `--script now.sh`.

## Silent runs (don't ping when nothing is happening)

A windowed job still fires on schedule even when no leg is live yet. Use the runtime's silent token (`[SILENT]` in Hermes — respond with exactly that and nothing else) to suppress delivery, otherwise the user gets a "nothing yet" message every interval. Send a real report only when at least one leg is live or newly settled, or the overall status changes.

## Telegram report rendering

Recurring scheduled updates should be sent as a single compact fenced `text` codeblock. Preserve source lines and the `Next check` line inside the block. Keep lines short enough for mobile scanning and avoid long paragraphs outside the block.

## Delivery notes

`deliver: origin` returns reports to the chat/session where tracking was started. Platform-specific failures should be handled by the running Hermes environment; do not put private paths or platform-specific internal troubleshooting in public reports.
