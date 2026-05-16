# Workflow: Stop Tracking

When the user asks to stop acca tracking:

1. List cron jobs.
2. Filter for names beginning with `acca-tracker-`.
3. If exactly one relevant job exists, remove it.
4. If multiple jobs exist, ask which one to stop or summarize the choices.
5. Confirm removal with the job name/ID.
6. State that no further scheduled updates will be sent.

Do not guess job IDs. Always list before removing.
