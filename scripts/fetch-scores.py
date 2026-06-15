#!/usr/bin/env python3
"""Pre-run score fetcher for acca-tracker cron jobs.

Why this exists: asking the LLM to fetch + parse a 50-event ESPN JSON on every
scheduled run is unreliable — it intermittently skips the call and hallucinates
a plausible score, which shows up as frozen or backwards clocks. This script
does the fetch deterministically and prints clean lines that Hermes injects into
the prompt, so the model only has to read, judge, and format authoritative data.

Usage: copy to ~/.hermes/scripts/acca-<id>.py, fill in SLIP + RUN_DATES for the
job, then create the cron job with `--script acca-<id>.py`. Its stdout is
prepended to the tracking prompt each run (and it also emits CURRENT TIME, so it
replaces a separate now.sh).
"""
import json, urllib.request, datetime, unicodedata

# ===== per-job config — the agent fills these in at job-creation time =====
# (leg number, home, away, kickoff date 'YYYYMMDD', selected team)
SLIP = [
    (1, "Germany", "Curaçao", "20260614", "Germany"),
    (2, "Netherlands", "Japan", "20260614", "Netherlands"),
    (3, "Spain", "Cape Verde", "20260615", "Spain"),
    (4, "Sweden", "Tunisia", "20260615", "Sweden"),
    (5, "Belgium", "Egypt", "20260615", "Belgium"),
]
# Dates this job should actually fetch: its RUN DATE + any spillover prev date.
RUN_DATES = ["20260615", "20260614"]
# ==========================================================================

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    for j in (" fc", " afc", " cf", " sc", " national team", "."):
        s = s.replace(j, "")
    return s.strip()

def fetch(date):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date}"
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return json.load(r).get("events", [])
    except Exception as e:
        return [{"_error": str(e)}]

# Fetch every relevant date and flatten. ESPN's `dates` filter uses a US
# calendar date, so a late-evening European kickoff can land under the previous
# day — searching the whole pool (not just the leg's nominal date) absorbs that.
all_events = []
for d in set(RUN_DATES):
    all_events += fetch(d)

def lookup(home, away, date):
    h, a = norm(home), norm(away)
    for e in all_events:
        if "_error" in e:
            return ("ERROR", e["_error"], "", "?", "?")
        comp = (e.get("competitions") or [{}])[0]
        cs = comp.get("competitors", [])
        names = [norm(c.get("team", {}).get("displayName", "")) for c in cs] + \
                [norm(c.get("team", {}).get("shortDisplayName", "")) for c in cs]
        if any(h == n or h in n or n in h for n in names) and \
           any(a == n or a in n or n in a for n in names):
            st = e.get("status", {})
            state = st.get("type", {}).get("state", "")
            desc = st.get("type", {}).get("description", "")
            clock = st.get("displayClock", "")
            score = {}
            for c in cs:
                score[norm(c.get("team", {}).get("displayName", ""))] = c.get("score")
            hs = next((v for k, v in score.items() if h == k or h in k or k in h), "?")
            as_ = next((v for k, v in score.items() if a == k or a in k or k in a), "?")
            return (state, desc, clock, hs, as_)
    return None

now = datetime.datetime.now().astimezone()
print(f"CURRENT TIME: {now.strftime('%Y-%m-%d %H:%M:%S %Z (%A)')}")
print("LIVE SCORES (authoritative ESPN fetch — judge and format from THESE; do not fetch yourself):")
for leg, home, away, date, sel in SLIP:
    if date not in RUN_DATES:
        print(f"  Leg {leg}: {home} vs {away} [{date}] -> future date, not checked this run")
        continue
    r = lookup(home, away, date)
    if r is None:
        print(f"  Leg {leg}: {home} vs {away} [{date}] -> NOT FOUND in ESPN feed (try fallback source)")
    elif r[0] == "ERROR":
        print(f"  Leg {leg}: {home} vs {away} [{date}] -> ESPN fetch error: {r[1]}")
    else:
        state, desc, clock, hs, as_ = r
        tag = {"pre": "NOT STARTED", "in": "LIVE", "post": "FINISHED"}.get(state, state.upper())
        clk = f" {clock}" if clock and state == "in" else ""
        print(f"  Leg {leg}: {home} {hs}-{as_} {away} [{date}] -> {tag} ({desc}){clk} | pick: {sel}")
