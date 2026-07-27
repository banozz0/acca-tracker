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
2. Try a structured check, especially the ESPN scoreboard API by date (TheSportsDB `eventsday` as a secondary structured cross-check).
3. Search readable public pages/snippets with team + date + competition terms.
4. Try official competition/team pages when aggregator pages are missing or stale.
5. If sources conflict, prefer the source that clearly matches both teams, date, competition, and status; otherwise keep the leg `UNVERIFIABLE` and continue tracking.

Keep the loop lightweight: no cookies, no login, no proxy rotation, no CAPTCHA bypass, no private endpoints, and no bookmaker scraping.

## ESPN scoreboard API (primary structured source)

ESPN exposes a free, unauthenticated JSON scoreboard that returns **live in-play** and final scores across most competitions. It is unofficial/undocumented but stable and widely used; keep the rest of the ladder underneath it as a fallback.

```text
https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates=YYYYMMDD
https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates=YYYYMMDD
```

- `{league}` examples: `eng.1` (Premier League), `esp.1` (La Liga), `ita.1` (Serie A), `ger.1` (Bundesliga), `fra.1` (Ligue 1), `uefa.champions`, `fifa.world`. Use `all` to sweep every competition for a date.
- `dates` is `YYYYMMDD` with no dashes.

Per event, read:

- `status.type.state` → `pre` (not started), `in` (live), `post` (finished).
- `status.type.description` → e.g. `Scheduled`, `First Half`, `Halftime`, `In Progress`, `Full Time`.
- `status.displayClock` → live match minute, e.g. `45'+2'`.
- `competitions[0].competitors[].score` plus `...team.abbreviation` / `displayName` → score and team matching.

Match by both teams + date, and confirm `state` and score before settling a leg. If the exact league code is unknown, query `all` for the date and filter by team names.

### Why ESPN stays primary (free alternatives evaluated 2026-07-27)

Live-tested against the same match day:

- **ESPN `all` scoreboard** — ~84 events on a Saturday, live in-play state + clock, no key. Clear winner.
- **TheSportsDB free tier** — returned only 3 events for the same day; final scores only, no live endpoint. Secondary cross-check only.
- **football-data.org** — free tier needs an API key and covers ~12 top competitions with tight rate limits. Optional keyed fallback, not a default.
- **fotmob unofficial API** — returned HTTP 404; unusable for automation.
- **OpenLigaDB** — reachable but German competitions only.

Re-evaluate if ESPN's unofficial endpoint breaks; until then it is the primary source and the ladder below covers gaps.

## TheSportsDB

TheSportsDB can be a useful structured public source for football events and scores.

Example endpoint:

```text
https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=YYYY-MM-DD&s=Soccer
```

Use it as a **secondary** structured cross-check, not the primary live source. The free tier (`eventsday.php`, key `3`) returns fixtures and **final** scores but has **no live in-play endpoint** and capped per-day coverage, so prefer the ESPN scoreboard API for live status and use TheSportsDB to confirm final results or fill coverage gaps. Some leagues, low-tier competitions, or event fields may also be missing or delayed.

Suggested use:

```text
1. Fetch the match date with `eventsday.php?d=YYYY-MM-DD&s=Soccer`.
2. Match both team names using normalized aliases.
3. Confirm league/date before trusting score/status fields.
4. If the event is absent or scores look stale, cross-check with the ESPN scoreboard API, reputable match centres, or official pages.
```

## Source priority

Use sources in this rough order, based on availability and match confidence:

1. **ESPN scoreboard API** (`site.api.espn.com/.../soccer/{league}/scoreboard?dates=YYYYMMDD`, or `/all/`) — primary structured source: free, no key, live in-play status + clock + final scores across most competitions.
2. TheSportsDB `eventsday.php` as a secondary structured cross-check for final scores and coverage gaps (free tier has **no live endpoint**).
3. ESPN, BBC Sport, Sky, TNT Sports, Guardian, or similar reputable match-centre web pages when the API is missing a fixture.
4. Official competition pages or official team match centres.
5. SofaScore or general search **snippets** as context only — direct SofaScore fetch is usually bot-blocked (see below).
6. `UNVERIFIABLE` when no reliable matching public source is found; continue tracking if the leg is not settled.

## SofaScore (low-priority, usually bot-blocked)

SofaScore direct fetches are usually blocked (HTTP 403 / Cloudflare) for automated tools, so treat it as a **last-resort snippet source, not a primary fetch target**. Only use SofaScore content that appears inside web-search result snippets, and only when it clearly matches both teams, the date/kickoff window, and competition. Do **not** describe SofaScore as an official public API, and do not attempt cookies, CAPTCHAs, proxies, private endpoints, or other bypass tactics.

If SofaScore is blocked, unreadable, stale, or ambiguous, mark `Source: SofaScore unavailable` or include it in `sources checked`, keep the leg `UNVERIFIABLE`, and continue scheduled tracking.

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
