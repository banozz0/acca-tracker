# Acca Tracker

Version: 2.9.0

Acca Tracker is a standalone Hermes skill for **read-only football accumulator/parlay tracking**.

It helps a Hermes agent parse a football betting slip, confirm the legs with the user, optionally create a bounded tracking job, and report whether each leg is alive, dead, won, pending, void, or unverifiable.

## What it does

- Parses football acca/parlay slips from text or screenshots.
- Shows a parsed preview before any tracking starts.
- Asks the user to confirm or correct the legs.
- Creates optional bounded Hermes cron jobs for status checks.
- Checks public score/status sources with a conservative retrieval ladder and cites them in reports.
- Uses compact Telegram/mobile-friendly status updates — one line per leg, no boilerplate footer.
- Sends only on change: the pre-run script diffs each leg's state+score against the previous run, so unchanged runs (including live matches where only the clock moved) stay silent instead of spamming every interval.
- Sends recurring tracker updates as compact fenced `text` codeblocks for cleaner mobile scanning.
- Reports each leg status and the overall acca status.
- Handles missing, ambiguous, or conflicting data as non-terminal `UNVERIFIABLE` instead of guessing.
- Optional P&L ledger: when configured, a settled acca appends one row (stake, price, outcome, return, running P&L) to a markdown ledger file — record-only, conservative settlement, no advice (see [`references/pnl-ledger.md`](references/pnl-ledger.md)).

## What it does not do

- No betting advice.
- No predictions or guaranteed outcomes.
- No “sure win”, “lock”, or hype framing.
- No odds optimization, staking plans, hedging, or cash-out advice.
- No chasing-losses framing.
- No bookmaker login, account integration, bet placement, or scraping bypass.
- No private ticket/account verification.

## Install

Copy the entire skill directory, not just `SKILL.md`; the skill references `docs/`, `knowledge/`, `workflows/`, `templates/`, and `examples/`.

Install into your active profile's skills tree:

```bash
git clone https://github.com/banozz0/acca-tracker.git
cd acca-tracker
PROFILE=default   # change to your Hermes profile name
mkdir -p ~/.hermes/profiles/"$PROFILE"/skills/acca-tracker
rsync -a --delete --exclude '.git' ./ \
  ~/.hermes/profiles/"$PROFILE"/skills/acca-tracker/
```

Avoid installing into `~/.hermes/skills` unless you intentionally want the default/shared profile skill location.

Then start a fresh Hermes session and load/use the skill by name; skill loading is session-cached.

## Validate the repo

```bash
python3 scripts/validate.py        # frontmatter, links, version sync, script unit tests
python3 scripts/test_fetch_scores.py   # score-fetcher unit tests only (offline)
python3 scripts/test_acca_ledger.py    # P&L ledger unit tests only (offline)
```

The same validation runs in CI on every push (`.github/workflows/validate.yml`).

## Verify after install

```bash
test -f ~/.hermes/profiles/"$PROFILE"/skills/acca-tracker/SKILL.md
python3 - "$PROFILE" <<'PY'
from pathlib import Path
import re, sys
p = Path.home()/f'.hermes/profiles/{sys.argv[1]}/skills/acca-tracker/SKILL.md'
s = p.read_text()
assert s.startswith('---')
m = re.search(r'\n---\s*\n', s[3:])
assert m
frontmatter = s[3:m.start()+3]
assert 'name: acca-tracker' in frontmatter
assert 'description:' in frontmatter
assert s[m.end()+3:].strip()
print('OK', p)
PY
hermes --profile "$PROFILE" tools list
```

## Required Hermes capabilities

Recommended toolsets:

- `vision` — parse screenshots/photos when supplied
- `web` — check public score/status sources
- `cronjob` — optional scheduled tracking jobs

Optional:

- `terminal` or code execution — useful for structured public APIs when available

## Supported market types

Best supported:

- Match result / 1X2
- Double chance
- Draw no bet
- Both teams to score: yes/no
- Total goals over/under
- Simple team goals over/under
- Basic handicap where the line and settlement rule are clear
- Corners, cards, and shots over/under — ESPN's feed carries live per-team stats for most fixtures; legs where the stat is missing are marked `UNVERIFIABLE` instead of guessed

Also supported:

- UFC fight winner — fights settle from ESPN's explicit winner flag; live fights stay pending (no fake "currently winning" mid-round)

Experimental:

- Basketball team markets (moneyline/totals) via the same ESPN feed (`basketball/nba`, `basketball/wnba`)

Limited or unsupported unless reliable source data is available:

- Offsides, possession, player props
- First/anytime goalscorer
- UFC method/round props (KO, submission, round betting)
- Complex bet builders
- Team to qualify / lift trophy / aggregate markets
- Bookmaker bonuses, boosts, insurance, or settlement-specific offers
- F1 (different ESPN data shape — on the roadmap, not supported yet)

See [`knowledge/bet-types.md`](knowledge/bet-types.md).

## Basic workflow

1. User sends a slip screenshot or text.
2. Hermes extracts only the tracking-relevant leg details and avoids repeating private identifiers.
3. Hermes shows a parsed preview with unclear fields marked.
4. User confirms or corrects the preview.
5. Hermes optionally creates a bounded tracking job.
6. Reports cite sources and mark uncertain data as `UNVERIFIABLE`.
7. User can stop tracking at any time.

See:

- [`workflows/parse-slip.md`](workflows/parse-slip.md)
- [`workflows/start-tracking.md`](workflows/start-tracking.md)
- [`workflows/stop-tracking.md`](workflows/stop-tracking.md)

## Example

See [`examples/sample-slip.md`](examples/sample-slip.md) for a sample parsed slip and status reports.

## Privacy notes

Betting slips can contain sensitive data. Before sharing a screenshot, redact:

- account IDs
- QR/barcodes
- ticket/slip numbers
- full names
- payment details
- bookmaker balances
- any personal identifiers

Tracking jobs may persist confirmed match details in Hermes scheduler state/output until they expire or are removed. Use a private chat for sensitive betting information.

## Runtime limitations

- Scheduled checks are not real-time alerts.
- Public score sources can lag, disagree, or omit lower leagues.
- Ambiguous team names may require user confirmation.
- Some markets cannot be verified from basic score data.
- Bookmaker settlement rules can differ from public match status.
- The skill does not verify actual bookmaker settlement.

See [`docs/runtime-notes.md`](docs/runtime-notes.md), [`docs/compact-report-format.md`](docs/compact-report-format.md), and [`knowledge/data-sources.md`](knowledge/data-sources.md).

## Responsible use

Use this skill only where gambling is legal for you and you meet local legal-age requirements. Do not use tracking updates to chase losses or increase stakes. If checking results feels stressful or compulsive, stop the tracking job and step away.

See [`docs/safety-and-responsible-use.md`](docs/safety-and-responsible-use.md).

## License

MIT. See [`LICENSE`](LICENSE).
