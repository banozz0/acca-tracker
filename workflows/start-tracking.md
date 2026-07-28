# Workflow: Start Tracking

Use this workflow only after the user confirms the parsed slip.

## Steps

1. Build a self-contained tracking prompt with confirmed legs, source rules, codeblock report format, and safety boundaries. For multi-date slips split into per-date jobs, every job's prompt must include the **full** confirmed slip (all legs), not just that date's legs — each run needs all legs to report overall status and to confirm games that finish after midnight.
2. Attach a per-job score script: copy `scripts/fetch-scores.py` to `~/.hermes/scripts/acca-<id>.py`, fill in its `SLIP` (each leg's teams, `YYYYMMDD` date, and market wording) and `RUN_DATES`, and create the job with `--script acca-<id>.py`. The prompt reads the injected `LIVE SCORES:` block instead of fetching — this is what keeps scores reliable (see SKILL.md "Scheduled agents are time-blind and fetch unreliably"). The script also writes a small `<name>.state.json` next to itself for change detection; runs where nothing changed stay `[SILENT]`.
3. Window the cron schedule to the slip's kickoff dates/times (hours band for the kickoff window; specific dates when known) and size `repeat` to reach the last match night. When kickoff times vary a lot across dates, create one windowed job per match date — see "Varied kickoff times across dates" in SKILL.md (handles spillover past midnight and timezone).
4. Set delivery to `origin` unless the user explicitly asks for another destination.
5. Name the job `acca-tracker-<short-id>`.
6. Tell the user:
   - job name
   - check interval
   - approximate expiry/repeat count
   - how to stop tracking
   - that persisted job state contains confirmed match details
7. Explain that reports are status-only and may mark legs `UNVERIFIABLE` when data is missing or ambiguous. State the status-only/no-advice boundary here, once — recurring updates do not carry a boundary footer.

## Safe default

```yaml
action: create
name: acca-tracker-<short-id>
schedule: "*/15 20-23 * * *"   # window to the match nights, not 24/7
repeat: 48                      # firings-per-window × number of match nights
deliver: origin
enabled_toolsets: [web]
```

Window the schedule to the kickoff times derived from the slip (`20-23` for a 21:00 KO; target specific dates like `13,15,18 6` when known). One windowed job covers a multi-day slip and stays silent between match nights. Never use `*/15 * * * *` for multi-day slips. Add optional toolsets only when supported by the running Hermes environment.

## Cron prompt status rules

Add these rules to every tracking prompt:

- `UNVERIFIABLE`, `DATA_UNAVAILABLE`, and `UNKNOWN` are non-terminal.
- Continue until all legs are final/settled, Hermes explicitly says max checks are reached, or the user stops the job.
- Never output `TRACKING COMPLETE` solely because source lookup failed, sources were blocked, all legs were unverifiable, or wall-clock time suggests the repeat window should be over.
- Return each recurring tracker update as a compact fenced `text` codeblock with `Next check` whenever tracking continues.
- Normalize team names and try aliases plus competition/date terms before giving up.
- Source priority: ESPN scoreboard API (live in-play + final scores) first, TheSportsDB eventsday as a final-score cross-check, ESPN/BBC/Sky/TNT/Guardian match-centre pages, official competition/team pages, then web-search snippets and `UNVERIFIABLE` and retry.
- SofaScore direct fetch is usually bot-blocked; use it only via search snippets and never call it an official public API.
- Keep unverifiable caveats short and non-repetitive: one source mismatch/failure note at the bottom is enough.
