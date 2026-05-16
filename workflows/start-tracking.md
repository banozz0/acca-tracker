# Workflow: Start Tracking

Use this workflow only after the user confirms the parsed slip.

## Steps

1. Build a self-contained tracking prompt with confirmed legs, source rules, and safety boundaries.
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
