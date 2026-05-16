# Workflow: Start Tracking

Use this workflow only after the user confirms the parsed slip.

## Steps

1. Build a self-contained tracking prompt with confirmed legs, source rules, codeblock report format, and safety boundaries.
2. Use a bounded cron schedule.
3. Set delivery to `origin` unless the user explicitly asks for another destination.
4. Name the job `acca-tracker-<short-id>`.
5. Tell the user:
   - job name
   - check interval
   - approximate expiry/repeat count
   - how to stop tracking
   - that persisted job state contains confirmed match details
6. Explain that reports are status-only and may mark legs `UNVERIFIABLE` when data is missing or ambiguous.

## Safe default

```yaml
action: create
name: acca-tracker-<short-id>
schedule: "*/15 * * * *"
repeat: 48
deliver: origin
enabled_toolsets: [web]
```

Avoid high-frequency schedules unless the user has a clear need and understands this is still not real-time. Add optional toolsets only when supported by the running Hermes environment.

## Cron prompt status rules

Add these rules to every tracking prompt:

- `UNVERIFIABLE`, `DATA_UNAVAILABLE`, and `UNKNOWN` are non-terminal.
- Continue until all legs are final/settled, max checks are reached, or the user stops the job.
- Never output `TRACKING COMPLETE` solely because source lookup failed.
- Return each recurring tracker update as a compact fenced `text` codeblock with `Next check` whenever tracking continues.
- Normalize team names and try aliases plus competition/date terms before giving up.
- Source priority: TheSportsDB/public structured data, SofaScore public page/search result when readable and clearly matched, ESPN/BBC/Sky/TNT/Guardian, official competition/team pages, fallback search, then `UNVERIFIABLE` and retry.
- Do not call SofaScore an official public API.
- Keep unverifiable caveats short and non-repetitive: one source mismatch/failure note at the bottom is enough.
