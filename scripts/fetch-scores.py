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
# (leg number, home, away, kickoff date 'YYYYMMDD', market wording from the slip
#  [, ESPN sport path — optional, defaults to "soccer/all"; e.g. "basketball/nba"])
SLIP = [
    (1, "Germany", "Curaçao", "20260614", "Match result: Germany win"),
    (2, "Netherlands", "Japan", "20260614", "Match result: Netherlands win"),
    (3, "Spain", "Cape Verde", "20260615", "Match result: Spain win"),
    (4, "Sweden", "Tunisia", "20260615", "Over 2.5 goals"),
    (5, "Belgium", "Egypt", "20260615", "Total corners over 8.5"),
]
# Dates this job should actually fetch: its RUN DATE + any spillover prev date.
RUN_DATES = ["20260615", "20260614"]
# ==========================================================================

DEFAULT_SPORT = "soccer/all"
# Team stats ESPN's scoreboard carries per competitor; printed for legs whose
# market mentions one of the keywords, so corner/card/shot markets are judgeable.
STAT_FIELDS = {"wonCorners": "corners", "yellowCards": "yellows",
               "redCards": "reds", "totalShots": "shots",
               "shotsOnTarget": "on target", "foulsCommitted": "fouls"}
STAT_KEYWORDS = ("corner", "card", "booking", "shot", "foul")

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


def fetch(sport, date):
    """Return (events, error) for one sport+date; never raises.

    MMA cards are one event holding many fights: each fight (competition) is
    flattened into its own event-shaped dict so lookup() works unchanged.
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard?dates={date}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            events = json.load(r).get("events", [])
    except Exception as e:
        return [], str(e)
    if sport.startswith("mma"):
        events = explode_fights(events)
    return events, None


def explode_fights(events):
    """One MMA card event -> one event-shaped dict per fight."""
    return [{"competitions": [c], "status": c.get("status", {})}
            for e in events for c in e.get("competitions", [])]


def competitor_names(c):
    side = c.get("team") or c.get("athlete") or {}
    return [side.get("displayName", ""), side.get("shortDisplayName", "")]


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

    def stats(c):
        return {s.get("name"): s.get("displayValue")
                for s in c.get("statistics", []) if s.get("name") in STAT_FIELDS}

    state = st.get("type", {}).get("state", "")

    def score(c):
        if c.get("score") is not None:
            return c.get("score")
        if state == "post":  # fight: no score, winner flag instead
            return "W" if c.get("winner") else "L"
        return "-"

    winner = next((competitor_names(c)[0] for c in (hc, ac)
                   if state == "post" and c.get("winner")), None)
    return {
        "state": state,
        "desc": st.get("type", {}).get("description", ""),
        "clock": st.get("displayClock", ""),
        "period": st.get("period"),
        "home_score": score(hc),
        "away_score": score(ac),
        "espn_home": competitor_names(hc)[0] or "?",
        "espn_away": competitor_names(ac)[0] or "?",
        "winner": winner,
        "weak": weakest <= 1,
        "home_stats": stats(hc),
        "away_stats": stats(ac),
    }


def stats_line(r, market):
    """home-away stat pairs for stat markets, e.g. 'corners 6-5, yellows 0-2'."""
    if not any(k in market.lower() for k in STAT_KEYWORDS):
        return ""
    parts = [f"{label} {r['home_stats'][f]}-{r['away_stats'][f]}"
             for f, label in STAT_FIELDS.items()
             if f in r["home_stats"] and f in r["away_stats"]]
    return ", ".join(parts)


def main():
    legs = [(l + (DEFAULT_SPORT,))[:6] for l in SLIP]
    pools, failed = {}, {}
    for sport, date in sorted({(l[5], l[3]) for l in legs if l[3] in RUN_DATES}):
        ev, err = fetch(sport, date)
        pools.setdefault(sport, []).extend(ev)
        if err:
            failed[(sport, date)] = err

    now = datetime.datetime.now().astimezone()
    print(f"CURRENT TIME: {now.strftime('%Y-%m-%d %H:%M:%S %Z (%A)')}")
    print("LIVE SCORES (authoritative ESPN fetch — judge and format from THESE; do not fetch yourself):")
    for (sport, d), err in failed.items():
        print(f"  WARNING: ESPN fetch failed for {sport} {d}: {err} — legs on that date need a fallback source")
    snapshot = {}
    for leg, home, away, date, market, sport in legs:
        head = f"  Leg {leg}: {home} vs {away} [{date}]"
        if date not in RUN_DATES:
            print(f"{head} -> future date, not checked this run")
            continue
        if (sport, date) in failed:
            print(f"{head} -> ESPN fetch failed for this date (try fallback source)")
            continue
        r = lookup(pools.get(sport, []), home, away)
        if r is None:
            print(f"{head} -> NOT FOUND in ESPN feed (try fallback source)")
            continue
        tag = {"pre": "NOT STARTED", "in": "LIVE", "post": "FINISHED"}.get(r["state"], r["state"].upper())
        clk = f" {r['clock']}" if r["clock"] and r["state"] == "in" else ""
        if clk and sport.startswith("mma") and r["period"]:
            clk = f" R{r['period']} {r['clock']}"
        stats = stats_line(r, market)
        snapshot[str(leg)] = f"{tag} {r['home_score']}-{r['away_score']}" + (f" [{stats}]" if stats else "")
        line = (f"  Leg {leg}: {home} {r['home_score']}-{r['away_score']} {away} "
                f"[{date}] -> {tag} ({r['desc']}){clk} | market: {market}")
        if r["winner"]:
            line += f" | winner: {r['winner']}"
        if stats:
            line += f" | stats: {stats}"
        elif any(k in market.lower() for k in STAT_KEYWORDS):
            line += " | stats: not in feed for this fixture — mark leg UNVERIFIABLE"
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
