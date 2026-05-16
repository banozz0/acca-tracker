# Data Sources

Acca Tracker uses public score/status information. Source availability varies by league, country, competition, match tier, and timing.

## Principles

- Prefer structured public data where available.
- Cite the source name or URL used for each leg.
- Cross-check if data is surprising, missing, ambiguous, or conflicting.
- Use `UNVERIFIABLE` instead of guessing.
- Treat lower-tier leagues and exotic markets as lower confidence.
- Do not bypass paywalls, CAPTCHAs, private endpoints, or anti-bot systems.

## Team matching

Before trusting a score, confirm the source matches:

- both teams
- competition/league when available
- date/kickoff window
- home/away orientation when relevant

If team names are ambiguous, translated, abbreviated, or shared by multiple clubs, ask the user to confirm league/date or mark the leg `UNVERIFIABLE`.

## TheSportsDB

TheSportsDB can be a useful structured public source for football events and scores.

Example endpoint:

```text
https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=YYYY-MM-DD&s=Soccer
```

Use it as one structured check when appropriate, but do not claim complete coverage. Some leagues, low-tier competitions, live statuses, or event fields may be missing or delayed.

## Web search fallback

Use web search for:

- finding official match pages
- finding club/league result pages
- cross-checking missing or conflicting scores
- context such as postponements or abandonment notices

Useful query patterns:

```text
<Team A> vs <Team B> live score
<Team A> <Team B> <competition> result <date>
<Team A> <Team B> official match report
```

## Confidence levels

Use a simple source confidence note when helpful:

- High: official league/club page, reputable live-score page, or structured source with matching teams/date.
- Medium: reputable search result/snippet with matching teams/date but limited detail.
- Low: partial match, unclear date, lower-tier source, stale data, or one-source-only confirmation.
- Unverifiable: no reliable matching source found or sources conflict.

## Unsupported data

Basic public score sources may not verify:

- corners
- cards
- shots
- player props
- bookmaker boosts
- private settlement decisions
- account-specific cash-out values

Mark these markets unverifiable unless a reliable public source includes the required data.
