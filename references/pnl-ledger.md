# P&L Ledger (optional)

The tracker reports whether a slip is alive/dead/won — this optional companion also **records what it paid**: one append-only markdown row per settled acca (stake, price, outcome, return, running P&L), written automatically when every leg is final.

It is a **record, not advice**. The safety boundary in `SKILL.md` applies in full: the ledger only writes down what the user already staked and what publicly verifiable results imply. No stake suggestions, no "win back" framing, ever.

## How it works

- `scripts/acca_ledger.py` is installed **once** into the profile scripts dir (same place as the per-job `acca-<id>.py` copies). It is never edited per job.
- At job creation the per-job script copy gets a small footer (below) with a `LEDGER` config. Each run the footer calls `acca_ledger.after_run(...)`, reusing the copy's own `fetch`/`lookup` — no duplicated ESPN logic.
- The hook stays silent (zero extra network) until the job's own `state.json` shows every gated leg `FINISHED`. Then it re-fetches once for structured final data (postponed/void descriptions, UFC winner, stats), settles each leg conservatively, computes the return, appends exactly one row, and writes an `acca-<id>.ledger.json` marker so the row is never duplicated.
- Everything it prints starts with `LEDGER:` and lands in the run's injected stdout. These lines are **status-only** (e.g. `LEDGER: recorded — Won · row appended to the ledger file`): stake, return, and P&L amounts never enter the prompt or any report — the numbers live only in the ledger file and the `.ledger.json` marker.

## Per-job footer (verbatim)

Append to the **end** of the per-job script copy, after filling `SLIP`/`RUN_DATES` as usual:

```python
# --- Optional P&L ledger hook (see references/pnl-ledger.md). Keep last in file. ---
LEDGER = {
    "path": "/absolute/path/to/vault/Agency/Betting ledger.md",
    "stake": "10.00",         # what the user actually staked
    "price": "6.20",          # combined decimal odds for the whole acca
    "currency": "€",
    "legs": "Arsenal W · Man City W · O2.5",  # compact human label for the row
    # per-leg decimal odds when visible — needed to recalculate a void leg; when
    # complete they are also sanity-checked against the combined price
    "leg_odds": {"1": "1.55", "2": "1.80", "3": "2.22"},
}
if __name__ == "__main__":
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import acca_ledger
        acca_ledger.after_run(SLIP, LEDGER, STATE_PATH, fetch, lookup, run_dates=RUN_DATES)
    except Exception as e:
        print(f"LEDGER: hook error ({e}) — scores above are unaffected")
```

Rules:

- Stake, combined price, and per-leg odds are captured at parse time (they are on the slip or the user states them). If stake or combined price is unknown, skip the ledger for this slip and say so — never guess money numbers.
- `path` is per-profile configuration: ask once, then persist it as `acca-ledger-defaults.json` (e.g. `{"path": "...", "currency": "€"}`) in the profile scripts dir so later sessions find it without asking again. The ledger file is created with proper frontmatter on the first settled acca (an existing note without a table gets a ledger table appended).
- Multi-date slips split into per-date jobs: add the footer to **exactly one** job — the one that observes the final whistle of the last leg (the spillover job when one exists). Its `RUN_DATES` gate the trigger; settlement judges the whole `SLIP`.
- Stake/price/return never go into the tracking prompt or recurring status updates; they live only in the per-job script file, the ledger file, and the `.ledger.json` marker. Every `LEDGER:` line printed into a run is status-only, amounts-free.
- The tracking prompt for a ledger-enabled job gets one extra rule (see the start-tracking workflow): include any injected `LEDGER:` line when a message is sent anyway, but never send because of one. The settle run always sends (legs just flipped to `FINISHED`), so the settlement note reaches the user exactly once.

## Settlement rules (conservative on purpose)

- Auto-settled: match result / moneyline, draw, double chance, draw no bet (draw → void), totals and team goals over/under on half- and whole-goal lines, BTTS, corners / shots / fouls lines from feed stats, cards lines **only when no red card was shown** (red-counting rules are bookmaker-specific), UFC fight winner from the explicit `winner:` flag.
- Never auto-settled (deny list → manual row): handicaps and any signed line, correct score, to nil / clean sheet, first/second-half markets, Asian quarter lines (x.25/x.75), booking points, race-to markets, winning margin, goalscorer markets, UFC method/round props. These have bookmaker-specific settlement that a score line cannot decide.
- Void handling is explicit, never silent: postponed / cancelled / abandoned legs and whole-line pushes void the leg — the combined price is divided by that leg's odds (`leg_odds`); an all-void acca returns the stake. A void leg with unknown odds is a manual ask, not a guess.
- Refuses to auto-settle (asks for a manual row instead): weak team-name matches, missing feed stats, finished fights with no winner (draw/NC), ambiguous wording, unsupported markets, unknown void-leg odds. A missing row beats a wrong one — money records do not get guessed.
- Corrections are **new rows** (stake `0.00`, Return set to the ± adjustment, short note in the Legs cell). Settled rows are never edited.

## Ledger file

Created on first write; one table, one row per settled acca:

```
| Date | Legs | Stake | Price | Outcome | Return | Running P&L |
|---|---|---|---|---|---|---|
| 2026-07-28 | Arsenal W · Man City W · O2.5 | €10.00 | 6.2 | Won | €62.00 | +€52.00 |
```

Running P&L is cumulative (`previous + return − stake`), parsed from the last table row — keep manual/correction rows in the same format, and keep this table the **only** table in the file. The Price cell echoes the configured string verbatim.

## Cleanup and caveats

- Stop-tracking removes `acca-<id>.ledger.json` together with the script and `state.json`; `acca_ledger.py` itself stays (shared across jobs).
- Stopping a tracker early: if the acca is already terminal but no `.ledger.json` marker exists, the row has NOT been written yet — either let the final job run through the last match night or add the row manually before removing the job.
- If the profile scripts dir is managed by a sync/backup that deletes unmanaged files, allowlist `acca_ledger.py` alongside the per-job scripts.
- If the ledger lives in a vault owned by a different account than the one editing it, fix file permissions after any manual row (e.g. `chmod 644`) so the scheduled hook can still append.
- The ledger file records real money outcomes — treat it like the slip itself (private chat, no account identifiers in the Legs label).
