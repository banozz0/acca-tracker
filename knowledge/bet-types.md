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

## Limited or unsupported

These often need data not available from basic public score feeds:

- corners
- cards
- shots/fouls/offsides
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
- Whole-goal lines: exact total may be `VOID`/push depending on bookmaker rule.
- Live overs that already exceed the line can be `WINNING`; unders remain vulnerable until final.

### Handicap

- Only evaluate when the handicap line and market wording are clear.
- If Asian-handicap quarter lines or bookmaker-specific settlement rules are unclear, mark `UNVERIFIABLE`.

## Overall acca status

- `WON` — every settled leg won and any void legs are accounted for.
- `ALIVE` — no leg is lost/dead, and at least one live leg is winning or pending.
- `PENDING` — no leg is lost/dead, but matches have not started or data is incomplete.
- `DEAD` — at least one leg is lost or dead.
- `UNVERIFIABLE` — one or more required legs cannot be verified from available public data; this does not complete tracking by itself.

## Reporting rule

If the bet type cannot be evaluated from available public data, say so directly and mark it `UNVERIFIABLE` instead of inventing logic. Keep tracking unless all legs are final/settled, max checks are reached, or the user stops it.
