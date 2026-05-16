# Acca Tracker

Version: 2.0.2

Acca Tracker is a standalone Hermes skill for **read-only football accumulator/parlay tracking**.

It helps a Hermes agent parse a football betting slip, confirm the legs with the user, optionally create a bounded tracking job, and report whether each leg is alive, dead, won, pending, void, or unverifiable.

## What it does

- Parses football acca/parlay slips from text or screenshots.
- Shows a parsed preview before any tracking starts.
- Asks the user to confirm or correct the legs.
- Creates optional bounded Hermes cron jobs for status checks.
- Checks public score/status sources with a conservative retrieval ladder and cites them in reports.
- Uses compact Telegram/mobile-friendly status updates.
- Sends recurring tracker updates as compact fenced `text` codeblocks for cleaner mobile scanning.
- Reports each leg status and the overall acca status.
- Handles missing, ambiguous, or conflicting data as non-terminal `UNVERIFIABLE` instead of guessing.

## What it does not do

- No betting advice.
- No predictions or guaranteed outcomes.
- No “sure win”, “lock”, or hype framing.
- No odds optimization, staking plans, hedging, or cash-out advice.
- No chasing-losses framing.
- No bookmaker login, account integration, bet placement, or scraping bypass.
- No private ticket/account verification.

## Install

Copy this folder into a Hermes skills directory, for example:

```bash
mkdir -p ~/.hermes/skills
cp -R acca-tracker ~/.hermes/skills/acca-tracker
```

Or install it into any profile-local Hermes skills directory managed by your Hermes setup.

Then start a fresh Hermes session and load/use the skill by name.

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

Limited or unsupported unless reliable source data is available:

- Corners, cards, fouls, shots, offsides
- First/anytime goalscorer
- Complex bet builders
- Team to qualify / lift trophy / aggregate markets
- Bookmaker bonuses, boosts, insurance, or settlement-specific offers

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
