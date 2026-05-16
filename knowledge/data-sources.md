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

## Conservative retrieval loop

Do not mark a normal top-flight/public fixture `UNVERIFIABLE` after a single failed lookup. Try a small bounded retrieval loop first:

1. Normalize the original slip names without losing them:
   - remove non-distinct suffix noise such as `FC`, `AFC`, `CF`, or `SC` when searching,
   - try obvious aliases/short names such as `Man United` / `Manchester United`,
   - keep city/reserve/youth/women markers when they are match-defining,
   - pair every alias with the competition/date to avoid false matches.
2. Try a structured/public check when useful, especially TheSportsDB by date.
3. Search readable public pages/snippets with team + date + competition terms.
4. Try official competition/team pages when aggregator pages are missing or stale.
5. If sources conflict, prefer the source that clearly matches both teams, date, competition, and status; otherwise keep the leg `UNVERIFIABLE` and continue tracking.

Keep the loop lightweight: no cookies, no login, no proxy rotation, no CAPTCHA bypass, no private endpoints, and no bookmaker scraping.

## TheSportsDB

TheSportsDB can be a useful structured public source for football events and scores.

Example endpoint:

```text
https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=YYYY-MM-DD&s=Soccer
```

Use it as one structured check when appropriate, but do not claim complete coverage. Some leagues, low-tier competitions, live statuses, or event fields may be missing or delayed.

Suggested use:

```text
1. Fetch the match date with `eventsday.php?d=YYYY-MM-DD&s=Soccer`.
2. Match both team names using normalized aliases.
3. Confirm league/date before trusting score/status fields.
4. If the event is absent, continue to SofaScore/search/official pages.
```

## Source priority

Use sources in this rough order, based on availability and match confidence:

1. TheSportsDB or another structured public source when available and suitable.
2. SofaScore public page or search result when normal readable content clearly matches teams/date/competition.
3. ESPN, BBC Sport, Sky, TNT Sports, Guardian, or similar reputable match centres.
4. Official competition pages or official team match centres.
5. General fallback search results for context.
6. `UNVERIFIABLE` when no reliable matching public source is found; continue tracking if the leg is not settled.

## SofaScore public-source fallback

SofaScore can be used as a normal public-source fallback, but only from readable public pages or search-result content. Do **not** describe SofaScore as an official public API. Do not use scraping bypasses, cookies, CAPTCHAs, proxies, private endpoints, or session tactics.

Use SofaScore only when the readable content clearly matches:

- both teams,
- match date/kickoff window,
- competition/league when needed, and
- score/status fields relevant to the market.

If the page is blocked, unreadable, stale, or ambiguous, mark `Source: SofaScore unavailable` or include it in `sources checked`, keep the leg `UNVERIFIABLE`, and continue scheduled tracking.

## Web search fallback

Use web search for:

- finding official match pages
- finding club/league result pages
- cross-checking missing or conflicting scores
- context such as postponements or abandonment notices

Useful query patterns:

```text
<Team A> vs <Team B> live score <date> <competition>
<Team A alias> <Team B alias> football result <date>
<Team A> <Team B> SofaScore <date>
<Team A> <Team B> ESPN BBC <competition>
<Team A> <Team B> <competition> result <date>
<Team A> <Team B> official match report
site:<league-or-club-domain> <Team A> <Team B> <date>
```

Avoid broad one-term searches such as only `<Team A> score`; they cause false matches and unnecessary `UNVERIFIABLE` results.

## Confidence levels

Use a simple source confidence note when helpful:

- High: official league/club page, reputable live-score page, or structured source with matching teams/date.
- Medium: reputable search result/snippet with matching teams/date but limited detail.
- Low: partial match, unclear date, lower-tier source, stale data, or one-source-only confirmation.
- Unverifiable: no reliable matching source found or sources conflict.

When unverifiable, keep the reason short in reports:

```text
Source: TheSportsDB/SofaScore/ESPN/BBC/search checked
Note: source date/competition mismatch; retrying.
```

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
