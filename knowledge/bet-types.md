# Bet Types

This reference describes conservative status logic for common football acca/parlay markets. Bookmaker settlement rules can differ, so reports should say when a rule is assumed or unclear.

## Officially supported categories

| Market | Public-score support | Notes |
| --- | --- | --- |
| Match result / 1X2 | Good | Usually settled on 90 minutes plus stoppage time unless slip says otherwise. |
| Double chance | Good | Team win/draw combinations from final score. |
| Draw no bet | Good | Draw is usually void/push. |
| Both teams to score | Good | Needs only final score. |
| Total goals over/under | Good | Half-goal lines are easiest. Whole-goal lines may push/void. |
| Team goals over/under | Good | Needs team score and line. |
| Basic handicap | Medium | Only if line and settlement rule are clear. |

## Stat markets (corners, cards, shots, fouls)

ESPN's scoreboard feed carries live per-team stats for most fixtures (`wonCorners`, `yellowCards`, `redCards`, `totalShots`, `shotsOnTarget`, `foulsCommitted`). The pre-run script prints them as a `stats:` line for legs whose market mentions corners/cards/bookings/shots/fouls, so these markets are supported **when the feed provides the stat for that fixture**:

| Market | Notes |
| --- | --- |
| Total / team corners over-under | From `corners H-A`. Half-lines settle cleanly. |
| Total / team cards over-under | Yellows + reds from the stats line. Confirm the slip's counting rule (e.g. red = 2 cards) — if unclear, say which rule was assumed. |
| Team shots / shots on target lines | From `shots` / `on target`. |

Status logic: over line already exceeded live -> `WINNING` (effectively secured, confirm at FT); under line already exceeded live -> `DEAD`; otherwise `PENDING` while live, and the FT stats decide `WON`/`LOST`. If the feed has no stats for the fixture (the script prints `stats: not in feed`), mark the leg `UNVERIFIABLE` — never guess stats, and never settle a stat market before full time.

## UFC fight winner

UFC legs use the `mma/ufc` sport path with fighter names in the home/away slots. The script reports `W-L` and an explicit `winner:` name once a fight is Final.

- `NOT STARTED` -> `PENDING`.
- `LIVE` -> `PENDING`, always. There is no reliable "currently winning" signal mid-fight; never mark a live fight `WINNING`.
- `FINISHED` + `winner:` matches the selection -> `WON`; matches the opponent -> `LOST`.
- `FINISHED` with no `winner:` (draw/no-contest) -> `UNVERIFIABLE` until a fallback source confirms the result type; most books void on NC.
- Method/round/prop markets (KO, submission, round betting) are unsupported — `UNVERIFIABLE`.

## Limited or unsupported

These often need data not available from public score/stat feeds:

- offsides, possession-based or player-prop markets
- first goalscorer / anytime goalscorer
- complex bet builders
- aggregate qualification markets
- bookmaker boosts, insurance, or settlement promotions

Use `UNVERIFIABLE` unless reliable source data is available.

## Status labels

- `WON` — final result clearly satisfies the leg.
- `WINNING` — live result currently satisfies the leg, but match is not final.
- `PENDING` — leg is not settled and remains possible.
- `LOST` — final result clearly fails the leg.
- `DEAD` — live result has already made the leg impossible, such as BTTS No after both teams score.
- `VOID` — source indicates postponement/cancellation or a push rule likely applies.
- `UNVERIFIABLE` — required data is unavailable, conflicting, ambiguous, or unsupported. This is non-terminal and should be retried while tracking continues.

## Conservative logic examples

### Match result

- Live: selected team winning → `WINNING`; drawing/losing → `PENDING`.
- Final: selected team won → `WON`; otherwise `LOST`.

### Double chance

- Live: selected outcomes currently satisfied → `WINNING`; otherwise `PENDING`.
- Final: selected outcomes satisfied → `WON`; otherwise `LOST`.

### Draw no bet

- Live: selected team winning → `WINNING`; drawing/losing → `PENDING`.
- Final: selected team won → `WON`; draw → `VOID`; selected team lost → `LOST`.

### Both teams to score: yes

- Live: both teams have scored → `WINNING`; otherwise `PENDING`.
- Final: both teams scored → `WON`; otherwise `LOST`.

### Both teams to score: no

- Live: neither/both-not-scored state can be `WINNING`, but if both teams score the leg is `DEAD`.
- Final: at least one team on zero → `WON`; both teams scored → `LOST`.

### Total goals over/under

- Half-goal lines: final total over/under line determines `WON` or `LOST`.
- Live over bets that already exceed the line can be `WINNING`/effectively satisfied, pending final/settlement confirmation.
- Live under bets become `DEAD` once the current total exceeds the line.
- Whole-goal lines: exact total may be `VOID`/push depending on bookmaker rule.
- If abandonment, void, Asian total, or bookmaker-specific settlement rules matter and are unclear, mark `UNVERIFIABLE`.

### Handicap

- Only evaluate when the handicap line and market wording are clear.
- If Asian-handicap quarter lines or bookmaker-specific settlement rules are unclear, mark `UNVERIFIABLE`.

## Overall acca status

- `WON` — every non-void settled leg won and all legs are terminal/settled.
- `LIVE` — no leg is lost/dead, and at least one live leg is currently satisfying its market.
- `PARTIAL` — at least one leg is settled/won/void and at least one remaining leg is pending/live/unverifiable, with no lost/dead leg.
- `PENDING` — no leg is lost/dead, and all unresolved legs are not started or awaiting data.
- `DEAD` — at least one leg is lost or dead.
- `UNVERIFIABLE` — one or more required legs cannot be verified from available public data; this is non-terminal unless the scheduler expires or the user stops tracking.

## Reporting rule

If the bet type cannot be evaluated from available public data, say so directly and mark it `UNVERIFIABLE` instead of inventing logic. Keep tracking unless all legs are final/settled, Hermes explicitly says the max-repeat run has been reached, or the user stops it.
