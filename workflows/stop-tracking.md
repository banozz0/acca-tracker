# Workflow: Stop Tracking

When the user asks to stop acca tracking:

1. List cron jobs.
2. Filter for names beginning with `acca-tracker-`.
3. If exactly one relevant job exists, remove it.
4. If multiple jobs exist, ask which one to stop or summarize the choices.
5. Confirm removal with the job name/ID.
6. State that no further scheduled updates will be sent.

Do not guess job IDs. Always list before removing.

If a per-job score script was created (`~/.hermes/profiles/<profile>/scripts/acca-<id>.py`), remove it and its `.state.json` sidecar together with the job. If a P&L ledger was configured, also remove the `acca-<id>.ledger.json` marker, but keep the shared `acca_ledger.py`. When the acca is already terminal and no `.ledger.json` marker exists, the ledger row has not been written yet — let the final job run through the last match night, or add the row manually before removing the job (see `../references/pnl-ledger.md`).
