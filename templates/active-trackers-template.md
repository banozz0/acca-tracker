# Active Trackers Template

This is a manual template only. Do not use the skill directory as runtime state.

Active tracker state should normally live in Hermes cron jobs and should expire or be removed with the job. If the user explicitly asks to keep a human-readable note, preview the exact content first and store only match/market details needed for tracking.

Never store ticket IDs, account IDs, QR/barcodes, names, payment details, balances, bookmaker credentials, or private settlement/account data.

## Template

```text
Tracker name: acca-tracker-<short-id>
Created: <date/time>
Expires: <date/time or repeat count>
Delivery: origin
Status: active / stopped / complete
Legs:
- <match> — <market> — <kickoff> — <public source notes>
Notes:
- No private ticket/account identifiers stored.
```
