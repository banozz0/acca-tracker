#!/usr/bin/env python3
"""Pre-run score fetcher for acca-tracker cron jobs.

Why this exists: asking the LLM to fetch + parse a 50-event ESPN JSON on every
scheduled run is unreliable — it intermittently skips the call and hallucinates
a plausible score, which shows up as frozen or backwards clocks. This script
does the fetch deterministically and prints clean lines that Hermes injects into
the prompt, so the model only has to read, judge, and format authoritative data.

Usage: copy to your profile's scripts dir —
~/.hermes/profiles/<profile>/scripts/acca-<id>.py (Hermes resolves `--script`
names against the profile scripts dir) — fill in SLIP + RUN_DATES for the job,
then create the cron job with `--script acca-<id>.py`. Its stdout is prepended
to the tracking prompt each run (and it also emits CURRENT TIME, so it replaces
a separate now.sh).
"""
import json, os, urllib.request, datetime, unicodedata

# ===== per-job config — the agent fills these in at job-creation time =====
# (leg number, home, away, kickoff date 'YYYYMMDD', market wording from the slip)
SLIP = [
    (1, "Germany", "Curaçao", "20260614", "Match result: Germany win"),
    (2, "Netherlands", "Japan", "20260614", "Match result: Netherlands win"),
    (3, "Spain", "Cape Verde", "20260615", "Match result: Spain win"),
    (4, "Sweden", "Tunisia", "20260615", "Over 2.5 goals"),
    (5, "Belgium", "Egypt", "20260615", "BTTS: yes"),
]
# Dates this job should actually fetch: its RUN DATE + any spillover prev date.
RUN_DATES = ["20260615", "20260614"]
# ==========================================================================

UA = {"User-Agent": "Mozilla/5.0 (acca-tracker score check)"}

# Last-seen state per leg, so runs where nothing changed can stay [SILENT].
# Lives next to this script; delete it together with the script when the job ends.
STATE_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".state.json"


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
    except Exception:
        pass  # state is an optimization; never let it break the score output


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    for j in (" fc", " afc", " cf", " sc", " national team", "."):
        s = s.replace(j, "")
    return s.strip()


def team_level(query, name):
    """How well a slip team name matches an ESPN team name.

    3 = exact, 2 = token subset (Bayern ⊆ Bayern Munich), 1 = weak prefix
    match (Man United ~ Manchester United — but also Niger ~ Nigeria, so
    level-1 matches are flagged in the output for the model to verify).
    """
    q, n = norm(query), norm(name)
    if not q or not n:
        return 0
    if q == n:
        return 3
    qt, nt = set(q.split()), set(n.split())
    if qt <= nt or nt <= qt:
        return 2
    if all(any(x.startswith(t) or t.startswith(x) for t in nt) for x in qt):
        return 1
    return 0


def fetch(date):
    """Return (events, error) for one date; never raises."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r).get("events", []), None
    except Exception as e:
        return [], str(e)


def competitor_names(c):
    t = c.get("team", {})
    return [t.get("displayName", ""), t.get("shortDisplayName", "")]


def lookup(events, home, away):
    """Best-scoring event where home and away match two DIFFERENT competitors.

    Returns None or a dict with state/desc/clock/scores, the ESPN names it
    matched, and weak=True when either side only matched at prefix level.
    """
    best = None
    for e in events:
        cs = (e.get("competitions") or [{}])[0].get("competitors", [])
        if len(cs) < 2:
            continue
        levels = []  # (home_level, away_level, home_comp, away_comp)
        for i, ci in enumerate(cs):
            for j, cj in enumerate(cs):
                if i == j:
                    continue
                hl = max(team_level(home, n) for n in competitor_names(ci))
                al = max(team_level(away, n) for n in competitor_names(cj))
                if hl and al:
                    levels.append((hl + al, min(hl, al), ci, cj))
        if not levels:
            continue
        score, weakest, hc, ac = max(levels, key=lambda x: (x[0], x[1]))
        if best is None or (score, weakest) > (best[0], best[1]):
            best = (score, weakest, e, hc, ac)
    if best is None:
        return None
    _, weakest, e, hc, ac = best
    st = e.get("status", {})
    return {
        "state": st.get("type", {}).get("state", ""),
        "desc": st.get("type", {}).get("description", ""),
        "clock": st.get("displayClock", ""),
        "home_score": hc.get("score", "?"),
        "away_score": ac.get("score", "?"),
        "espn_home": hc.get("team", {}).get("displayName", "?"),
        "espn_away": ac.get("team", {}).get("displayName", "?"),
        "weak": weakest <= 1,
    }


def main():
    events, failed = [], {}
    for d in sorted(set(RUN_DATES)):
        ev, err = fetch(d)
        events += ev
        if err:
            failed[d] = err

    now = datetime.datetime.now().astimezone()
    print(f"CURRENT TIME: {now.strftime('%Y-%m-%d %H:%M:%S %Z (%A)')}")
    print("LIVE SCORES (authoritative ESPN fetch — judge and format from THESE; do not fetch yourself):")
    for d, err in failed.items():
        print(f"  WARNING: ESPN fetch failed for {d}: {err} — legs on that date need a fallback source")
    snapshot = {}
    for leg, home, away, date, market in SLIP:
        head = f"  Leg {leg}: {home} vs {away} [{date}]"
        if date not in RUN_DATES:
            print(f"{head} -> future date, not checked this run")
            continue
        if date in failed:
            print(f"{head} -> ESPN fetch failed for this date (try fallback source)")
            continue
        r = lookup(events, home, away)
        if r is None:
            print(f"{head} -> NOT FOUND in ESPN feed (try fallback source)")
            continue
        tag = {"pre": "NOT STARTED", "in": "LIVE", "post": "FINISHED"}.get(r["state"], r["state"].upper())
        clk = f" {r['clock']}" if r["clock"] and r["state"] == "in" else ""
        snapshot[str(leg)] = f"{tag} {r['home_score']}-{r['away_score']}"
        line = (f"  Leg {leg}: {home} {r['home_score']}-{r['away_score']} {away} "
                f"[{date}] -> {tag} ({r['desc']}){clk} | market: {market}")
        if r["weak"]:
            line += (f" | WEAK NAME MATCH — ESPN fixture is '{r['espn_home']} vs "
                     f"{r['espn_away']}': verify this is the right game before using the score")
        print(line)

    # Change detection: compare state+score per leg against the previous run so
    # the agent can stay [SILENT] on runs where nothing moved (no clock spam —
    # the live match minute is deliberately NOT part of the snapshot).
    old = load_state()
    changes = [f"Leg {leg}: {old.get(leg, 'first check')} -> {val}"
               for leg, val in snapshot.items() if old.get(leg) != val]
    save_state({**old, **snapshot})
    if changes:
        print("CHANGE SINCE LAST RUN: YES — " + "; ".join(changes))
    else:
        print("CHANGE SINCE LAST RUN: NO — same states and scores as the previous check")


if __name__ == "__main__":
    main()
