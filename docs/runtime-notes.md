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

```yaml
action: create
name: acca-tracker-<short-id>
schedule: "*/15 * * * *"
repeat: 48
deliver: origin
enabled_toolsets: [web]
```

Use bounded repeat counts. Avoid excessive polling; this is not a real-time goal-alert system. Add other toolsets only when the running Hermes environment supports them and the job genuinely needs them.

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
- the bounded max-check/repeat count is reached, or
- the user stops the tracker.

Never say `TRACKING COMPLETE` only because public lookup failed, a source was blocked, or all legs were unverifiable on a check. In those cases, include `Next check` and retry later.

## Telegram report rendering

Recurring scheduled updates should be sent as a single compact fenced `text` codeblock. Preserve source lines and the `Next check` line inside the block. Keep lines short enough for mobile scanning and avoid long paragraphs outside the block.

## Delivery notes

`deliver: origin` returns reports to the chat/session where tracking was started. Platform-specific failures should be handled by the running Hermes environment; do not put private paths or platform-specific internal troubleshooting in public reports.
