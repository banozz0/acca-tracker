#!/usr/bin/env python3
"""Optional P&L ledger companion for acca-tracker (see references/pnl-ledger.md).

Why this exists: the tracker reports whether a slip is alive/dead/won but never
records what it paid. This module turns a settled acca into exactly one
append-only row in a markdown ledger — stake, price, outcome, return, running
P&L — written by the per-job pre-run script at the moment every leg is final.

It is deliberately NOT wired into fetch-scores.py. The start-tracking workflow
adds a small footer to the per-job script copy that calls `after_run(...)`,
passing the copy's own `fetch`/`lookup` so the ESPN layer is not duplicated.
Money logic is conservative: any leg it cannot settle beyond doubt becomes a
"add the row manually" ask instead of a wrong number in a financial record.

Install once per profile: copy this file unchanged to the profile scripts dir
(same directory as the per-job `acca-<id>.py` copies).
"""
import json
import os
import re
import unicodedata
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_SPORT = "soccer/all"
CENT = Decimal("0.01")
# ESPN status descriptions that void a leg regardless of the reported score.
VOID_DESCS = ("postpon", "cancel", "abandon", "suspend")
STAT_KEYWORDS = ("corner", "card", "booking", "shot", "foul")
# Markets whose bookmaker settlement cannot be derived from a final
# score/stat line (bet-types.md "limited or unsupported") — never auto-settled.
DENY_PATTERNS = (
    r"handicap", r"\bah\b", r"correct score", r"to nil", r"clean sheet",
    r"\bhal[fv]", r"\bht\b", r"\b1st\b", r"\b2nd\b", r"\b[12]h\b",
    r"booking point", r"race to", r"winning margin", r"scorecast", r"goalscorer",
)
MMA_PROP_PATTERNS = (r"\bround\b", r"\bko\b", r"submission", r"\bmethod\b",
                     r"\bdecision\b", r"inside the distance")
# The generic result branch only fires on wording that clearly is a result bet.
RESULT_WORDS = (r"\b(win|wins|won|beat|beats|victory|moneyline|1x2|"
                r"match result|match winner|draw|double chance)\b")

LEDGER_HEADER = "| Date | Legs | Stake | Price | Outcome | Return | Running P&L |"

SCAFFOLD = """---
type: reference
created: {today}
updated: {today}
owner: acca-tracker
tags: [betting, ledger, pnl]
---

# 📒 Betting Ledger

**Append-only P&L record — one row per settled acca, written automatically by the acca-tracker settle hook.**

## 📊 Ledger

{header}
|---|---|---|---|---|---|---|

## 🧠 How this file works

- A row is appended when a tracked acca reaches a terminal state (won / lost / void). Rows are never edited afterwards.
- A correction is a NEW row: stake 0.00, Return set to the adjustment amount (± the error), with a short note in Legs. Running P&L heals from there.
- Void legs are recalculated explicitly (combined price divided by the void leg's odds); pushes on whole-goal lines count as void.
- Anything the settle logic cannot judge beyond doubt is left for a manual row — a missing row beats a wrong one.
- Keep this as the only markdown table in the file: the running total is read from the last table row.

## 🔗 Related
- [[Operating Baseline]]
"""


def _norm(s):
    """Lowercase, strip accents and punctuation — for word-level matching."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def _mentions(market, name):
    """Does the market wording name this team/fighter? Full-name phrase match,
    else any distinctive (4+ char) token of the name appearing as a word."""
    m, n = f" {_norm(market)} ", _norm(name)
    if f" {n} " in m:
        return True
    return any(f" {t} " in m for t in n.split() if len(t) >= 4)


def _ou_line(market):
    """('over'|'under', Decimal line) or None — parsed from the raw wording so
    the decimal point survives (normalization would split '2.5')."""
    m = re.search(r"\b(over|under)\s*(\d+(?:\.\d+)?)", market.lower())
    return (m.group(1), Decimal(m.group(2))) if m else None


def _ou_settle(direction, line, total):
    if line % Decimal("0.5") != 0:
        return "UNVERIFIABLE", f"asian/quarter line {line} — split settlement is bookmaker-specific"
    total = Decimal(total)
    if total == line:
        return "VOID", f"push on the {line} line"
    hit = total > line if direction == "over" else total < line
    return ("WON" if hit else "LOST"), f"{direction} {line}, landed {total}"


def _stat_value(r, side, field):
    stats = r["home_stats"] if side == "home" else r["away_stats"]
    if field not in stats:
        return None
    try:
        return int(float(stats[field]))
    except (TypeError, ValueError):
        return None


def _settle_stat(market, ou, home, away, r):
    lower = market.lower()
    if "card" in lower or "booking" in lower:
        reds = [_stat_value(r, s, "redCards") for s in ("home", "away")]
        if None in reds:
            return "UNVERIFIABLE", "red-card count not in feed"
        if sum(reds):
            return "UNVERIFIABLE", "red card shown — card-counting rule is bookmaker-specific"
        field = "yellowCards"
    elif "corner" in lower:
        field = "wonCorners"
    elif "foul" in lower:
        field = "foulsCommitted"
    else:  # shots
        field = "shotsOnTarget" if "on target" in lower else "totalShots"
    sides = [s for s, name in (("home", home), ("away", away)) if _mentions(market, name)]
    if len(sides) == 2:
        return "UNVERIFIABLE", "market names both teams — ambiguous"
    values = [_stat_value(r, s, field) for s in (sides or ["home", "away"])]
    if None in values:
        return "UNVERIFIABLE", "stat not in feed for this fixture"
    return _ou_settle(ou[0], ou[1], sum(values))


def _settle_mma(market, home, away, r):
    if not r["winner"]:
        return "UNVERIFIABLE", "finished with no winner (draw/no-contest)"
    picked_home, picked_away = _mentions(market, home), _mentions(market, away)
    if picked_home == picked_away:
        return "UNVERIFIABLE", "cannot tell which fighter the market picked"
    winner_side = "home" if r["winner"] == r["espn_home"] else "away"
    won = (winner_side == "home") == picked_home
    return ("WON" if won else "LOST"), f"winner: {r['winner']}"


def settle_leg(leg, result):
    """(outcome, reason) for one leg from a final lookup() result.

    Outcomes: WON | LOST | VOID | UNVERIFIABLE. Conservative on purpose —
    UNVERIFIABLE means "ask for a manual row", never "guess".
    """
    home, away, market = leg[1], leg[2], leg[4]
    sport = leg[5] if len(leg) > 5 else DEFAULT_SPORT
    if result is None:
        return "UNVERIFIABLE", "match not found in feed"
    if result["state"] != "post":
        # checked before the void words so a temporarily suspended live match
        # is "not final", not void
        return "UNVERIFIABLE", "not final in feed"
    if any(k in result["desc"].lower() for k in VOID_DESCS):
        return "VOID", result["desc"]
    if result["weak"]:
        return "UNVERIFIABLE", "weak team-name match — will not settle money on it"

    norm_m = _norm(market)
    if re.search(r"[+-]\s?\d", market) or any(re.search(p, norm_m) for p in DENY_PATTERNS):
        return "UNVERIFIABLE", "market type not auto-settled"

    if sport.startswith("mma"):
        if any(re.search(p, norm_m) for p in MMA_PROP_PATTERNS):
            return "UNVERIFIABLE", "fight prop markets are not auto-settled"
        return _settle_mma(market, home, away, r=result)

    ou = _ou_line(market)
    if any(k in market.lower() for k in STAT_KEYWORDS):
        if not ou:
            return "UNVERIFIABLE", "stat market without a clear over/under line"
        return _settle_stat(market, ou, home, away, result)

    try:
        hs, aw = int(result["home_score"]), int(result["away_score"])
    except (TypeError, ValueError):
        return "UNVERIFIABLE", "no numeric final score in feed"

    if ou:  # goals total, or a single team's goals when the wording names one
        picked = [s for s, name in (("home", home), ("away", away)) if _mentions(market, name)]
        if len(picked) == 2:
            return "UNVERIFIABLE", "market names both teams — ambiguous"
        total = hs + aw if not picked else (hs if picked[0] == "home" else aw)
        return _ou_settle(ou[0], ou[1], total)

    if "both teams to score" in norm_m or "btts" in norm_m:
        both = hs > 0 and aw > 0
        want_no = bool(re.search(r"\bno\b", norm_m))
        return ("WON" if both != want_no else "LOST"), f"final {hs}-{aw}"

    outcome_side = "home" if hs > aw else "away" if aw > hs else "draw"
    if "draw no bet" in norm_m:
        picked = [s for s, name in (("home", home), ("away", away)) if _mentions(market, name)]
        if len(picked) != 1:
            return "UNVERIFIABLE", "cannot tell which team draw-no-bet picked"
        if outcome_side == "draw":
            return "VOID", "draw no bet — draw"
        return ("WON" if outcome_side == picked[0] else "LOST"), f"final {hs}-{aw}"

    # Match result / moneyline / double chance: the wording picks 1–2 of
    # home / away / draw; the final score picks exactly one. Two picks are
    # only a real double chance when the wording says so ("or"/"double
    # chance") — otherwise both teams matching means ambiguity, not a bet.
    if not re.search(RESULT_WORDS, norm_m):
        return "UNVERIFIABLE", "unsupported market for auto-settle"
    picked = {s for s, name in (("home", home), ("away", away)) if _mentions(market, name)}
    if re.search(r"\bdraw\b", norm_m):
        picked.add("draw")
    double = "double chance" in norm_m or re.search(r"\bor\b", norm_m)
    if len(picked) == 1 or (len(picked) == 2 and double):
        return ("WON" if outcome_side in picked else "LOST"), f"final {hs}-{aw}"
    if len(picked) == 2:
        return "UNVERIFIABLE", "market matches both teams — ambiguous"
    return "UNVERIFIABLE", "unsupported market for auto-settle"


def acca_return(stake, price, outcomes, leg_odds):
    """(label, return amount) for the whole acca, or (None, reason) when it
    needs a manual row. Void legs divide their odds out of the combined price;
    an all-void acca returns the stake."""
    stake, price = Decimal(stake), Decimal(price)
    if any(o == "LOST" for o in outcomes.values()):
        return "Lost", Decimal("0").quantize(CENT)
    voids = sorted(n for n, o in outcomes.items() if o == "VOID")
    if len(voids) == len(outcomes):
        return "Void — all legs, stake returned", stake.quantize(CENT)
    if leg_odds and all(str(n) in leg_odds for n in outcomes):
        # cheap typo guard on a money record: per-leg odds must roughly
        # multiply back to the combined price. Only the winning path uses the
        # price, so lost/all-void accas above settle regardless. The reason is
        # number-free — it gets printed into the cron prompt.
        product = Decimal("1")
        for n in outcomes:
            product *= Decimal(str(leg_odds[str(n)]))
        if abs(product - price) > price * Decimal("0.05"):
            return None, "per-leg odds do not multiply to the combined price — check the LEDGER config"
    effective = price
    for n in voids:
        odds = (leg_odds or {}).get(str(n))
        if not odds:
            return None, f"leg {n} is void but its odds are unknown — cannot recalculate the return"
        effective /= Decimal(str(odds))
    label = "Won" if not voids else f"Won ({len(voids)} leg void)"
    return label, (stake * effective).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(currency, amount):
    amount = Decimal(amount).quantize(CENT)
    sign = "-" if amount < 0 else ""
    return f"{sign}{currency}{abs(amount):.2f}"


def _last_running_total(text):
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    if not rows:
        return Decimal("0")
    last_cell = rows[-1].strip().strip("|").split("|")[-1].strip()
    try:
        return Decimal(re.sub(r"[^0-9.\-]", "", last_cell))
    except Exception:
        return Decimal("0")  # header or separator row — ledger is empty


def _append_row(path, config, label, ret):
    today = date.today().isoformat()
    stake = Decimal(config["stake"])
    currency = config.get("currency", "€")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if not os.path.exists(path) or not open(path).read().strip():
        with open(path, "w") as f:
            f.write(SCAFFOLD.format(today=today, header=LEDGER_HEADER))
    text = open(path).read()
    running = _last_running_total(text) + ret - stake
    legs = str(config.get("legs") or "").replace("|", "/") or "(legs not recorded)"
    row = (f"| {today} | {legs} | {_money(currency, stake)} | {config['price']} "
           f"| {label} | {_money(currency, ret)} "
           f"| {'+' if running >= 0 else ''}{_money(currency, running)} |")
    lines = text.splitlines()
    pipe_rows = [i for i, l in enumerate(lines) if l.strip().startswith("|")]
    if not pipe_rows:  # note existed already but has no table yet — add one
        lines += ["", "## 📊 Ledger", "", LEDGER_HEADER, "|---|---|---|---|---|---|---|"]
        pipe_rows = [len(lines) - 1]
    lines.insert(pipe_rows[-1] + 1, row)
    text = re.sub(r"^updated: .*$", f"updated: {today}", "\n".join(lines) + "\n",
                  count=1, flags=re.M)
    with open(path, "w") as f:
        f.write(text)
    return running


def after_run(slip, config, state_path, fetch, lookup, run_dates=None):
    """Per-job hook entry point — called after main() by the per-job script's
    footer. Must never break the score output: everything is caught.

    For a slip split into per-date jobs, add the footer to the LAST job only
    (the one that sees the final whistle) and pass its RUN_DATES: the trigger
    then waits for that job's own legs, while settlement re-fetches and judges
    every leg of the full slip."""
    try:
        _run(slip, config or {}, state_path, fetch, lookup, run_dates)
    except Exception as e:  # a ledger bug must never cost the score report
        print(f"LEDGER: hook error ({e}) — no row written")


def _run(slip, config, state_path, fetch, lookup, run_dates):
    marker_path = state_path.replace(".state.json", ".ledger.json")
    if os.path.exists(marker_path):
        return  # row already written for this acca
    try:
        with open(state_path) as f:
            state = json.load(f)
    except Exception:
        return  # no state yet — nothing can be settled
    legs = [(l + (DEFAULT_SPORT,))[:6] for l in slip]
    gate = [l for l in legs if not run_dates or l[3] in run_dates]
    if not gate or not all(str(l[0]) in state and state[str(l[0])].startswith("FINISHED")
                           for l in gate):
        return  # not terminal yet — stay silent, zero extra network

    try:
        stake, price = Decimal(config["stake"]), Decimal(config["price"])
        assert config["path"] and stake > 0 and price > 1
    except Exception:
        print("LEDGER: acca settled but ledger config is incomplete "
              "(need path, stake, price) — add the row manually")
        return

    # One structured re-fetch across every slip date: settling needs the final
    # description (postponed/void), winner and stats, which the state snapshot
    # deliberately does not carry.
    pools, failed = {}, []
    for sport, day in sorted({(l[5], l[3]) for l in legs}):
        events, err = fetch(sport, day)
        pools.setdefault(sport, []).extend(events)
        if err:
            failed.append(f"{sport} {day}: {err}")
    if failed:
        print(f"LEDGER: final re-fetch failed ({'; '.join(failed)}) — will retry next run")
        return

    outcomes, notes, stuck = {}, [], []
    for leg in legs:
        outcome, reason = settle_leg(leg, lookup(pools.get(leg[5], []), leg[1], leg[2]))
        outcomes[str(leg[0])] = outcome
        notes.append(f"leg {leg[0]} {outcome}")
        if outcome == "UNVERIFIABLE":
            stuck.append(f"leg {leg[0]}: {reason}")
    if stuck:
        print(f"LEDGER: acca finished but could not be auto-settled ({'; '.join(stuck)}) "
              "— add the ledger row manually")
        return

    label, ret = acca_return(stake, price, outcomes, config.get("leg_odds"))
    if label is None:
        print(f"LEDGER: {ret} — add the ledger row manually")
        return
    running = _append_row(config["path"], config, label, ret)
    with open(marker_path, "w") as f:
        json.dump({"recorded": date.today().isoformat(), "outcome": label,
                   "return": str(ret), "running": str(running),
                   "legs": "; ".join(notes)}, f)
    # Status only — this line is injected into the cron prompt, and stake/
    # return amounts never enter prompts or reports (SKILL.md privacy rule).
    # The numbers live in the ledger file and the marker.
    print(f"LEDGER: recorded — {label} · row appended to the ledger file")
