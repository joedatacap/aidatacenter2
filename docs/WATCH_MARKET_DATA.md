# Market snapshot model and refresh

Market prices and size context are separate from the reviewed financial snapshot. The market builder never writes `watch_*.json`, the financial `data.json` or its research cutoff. This implementation is an explicit, manually run cached-data workflow; it does not configure a live feed or recurring market refresh.

## Current availability

The committed `neocloud/data/market_snapshot.json` is an honest gap manifest. Its availability check was **2026-11-22T00:28:36Z**; its price observation timestamp is **null**. No usable price-history export with verified permission for public static display, redistribution and downloadable cached closes was acquired. There are no real prices or return series in this file. See `WATCH_MARKET_SOURCES.md` for source and license investigation.

The existing six unblocked manually reviewed market-cap observations remain dated November 13, with their original source URLs and provider-defined basic-capitalization caveat. They are labelled `dated_manual`, not newly refreshed. Nebius, SharonAI and Axe retain their capitalization blockers and **Size unverified**, even if a new price series is later available. A feed value cannot clear those blockers. A price-only refresh retains the latest verified size observation under the same provider and grant. A newer unresolved observation still carries its blocker. No weighted-average EPS share count is used.

## Calendar and windows

`neocloud/data/market_calendar.json` is a finite, reviewed US equity core-session schedule covering December 2025 through December 2026. NYSE/ICE and Nasdaq primary calendars establish holiday closures and 13:00 Eastern early closes. Ordinary closes are 16:00 `America/New_York`, converted to UTC with daylight-saving rules. Every covered weekday must be explicitly either a session or a sourced closure; omitted weekdays do not silently become holidays.

At the recorded November 22 availability check, the latest completed session is **November 20, 2026, 21:00 UTC**. An expiration Friday is not an exchange holiday. Before the current day's confirmed close, the preceding completed session is used. A calendar whose coverage has expired cannot establish a new expected endpoint.

Each return uses one common confirmed end session. The start target is seven calendar days earlier for 1W, one or three calendar months earlier (clamped to the destination month's last day) for 1M/3M, and December 31 of the prior year for YTD. Use the preceding confirmed exchange close when a start target is not a trading date. Actual start/end dates stay on every return. A company's stale close is displayed with its own date and never substituted for another company's endpoint.

The preferred basis is `split_adjusted_price_return`, excluding dividends: `(end adjusted close / start adjusted close − 1) × 100`. A provider's dividend-adjusted series must instead be labelled `total_return`. The two methods cannot mix silently. Literal closing quotes are separate `price` observations; adjusted closes or total-return index levels are **never** presented as a literal stock quote.

## Reviewed input contract

The refresh command accepts a local JSON export from a permitted provider. The exporter holds credentials server-side. No key, authenticated download URL, request header or arbitrary raw provider object enters the public cache.

Required top-level fields:

- `schema_version: 1`, `observed_at` with explicit UTC offset, and `provider`.
- Provider fields: `name`, public HTTPS `source_url`, `permission_url`, `permission_excerpt`, `terms_reviewed_at`, `permission_status: "verified_public_display"`, and **all three** booleans `public_display_permitted`, `public_redistribution_permitted`, `cached_history_permitted` set to true. Optional `attribution_text` is bounded plain text (no HTML), preserved beside the provider source link for required public attribution. These are an audit record of an actual reviewed entitlement, not a way to override vendor terms. Permission must cover downloadable closes in static HTML/JSON exports, not merely a private API call or a non-cacheable quote widget.
- `provider.price_basis`: `split_adjusted_price_return` or `total_return`.
- `calendar`: `exchange`, `confirmed: true`, public `source_url`, `verified_at`, `coverage_start`, `coverage_end`, explicit `sessions: [{date, close_at}]`, and `closed_sessions: [{date, reason}]`. The checked-in reviewed calendar may be used while its coverage remains current.
- `companies`: canonical `id`, `ticker`, `listing_status`, `exchange` (`XNYS`/`XNAS` or NYSE/NASDAQ), `currency: "USD"`, optional actual `listed_on`, and `prices: [{date, close}]`. Missing prices stay missing. An optional per-point `basis` must match the global method.
- Literal quote, when verified: `quote: {value, date, currency, exchange, kind: "closing_price", source_url}`. If omitted, returns may still be valid but the stock-price cell remains unavailable.
- Optional `market_cap: {value, currency: "USD", as_of, status: "verified", share_basis, source_url, ratio_blocker?}`. Its share basis must describe a dated outstanding-share capitalization, not weighted-average EPS shares. Missing newer values preserve the earlier manually reviewed dated size context.
- Corporate actions: `corporate_actions: [{effective_date, type, verified, source_url, series_treatment, ratio?, from_ticker?, to_ticker?}]`. Splits/reverse splits need a positive ratio and `series_treatment: "reflected_in_series"`. Verified ticker chains must be chronological and end at the canonical ticker; historical price symbols must match their actual interval. A normalized vendor predecessor series must explicitly set `predecessor_series_verified: true`. Dividend treatment is `excluded_from_price_return` or `included_in_total_return`, matching the method.

No future observation, licensing review, calendar verification or uncompleted-session close is accepted. Credential-bearing URLs and arbitrary inner calendar/action fields are rejected or excluded from public output.

An unverified action, missing session or unexplained move exceeding 2×/below 0.5× creates a history boundary. That threshold is a review trigger, not proof of a split. An independently reviewed legitimate large move may explicitly include per-point `continuity_verified: true` and a public `continuity_source_url`. The default refuses to draw a continuous line or infer a full-window return through an unverified boundary.

## Normalized history

Selected companies normalize to 100 on the same actual common date. The model uses the intersection of their current contiguous verified segments; all require the common confirmed endpoint and at least two common closes. An IPO or verified-history limitation can shorten the normalized comparison; the shortened start and reason are explicit. A full 1M return can remain unavailable while a shorter common comparison is valid. No interpolation, extrapolation or bridge across an unverified split, ticker transition, suspension or missing session is performed.

## Refresh procedure

Install the project's Python dependencies as in the release runbook, then run:

```sh
python scripts/refresh_market_snapshot.py --input /secure/path/reviewed-provider-export.json
npm run build:watch
```

For reproducible tests or an explicitly recorded review cutoff, add `--now 2026-11-22T00:28:36Z`. A future production refresh should use its actual run time, not this historical example. Provider exports and credentials must remain outside committed/public assets.

The CLI validates the complete candidate before replacing `neocloud/data/market_snapshot.json`. It serializes concurrent writers, rejects older observation/end sessions, flushes a temporary file and atomically replaces the cache. A malformed, unlicensed or coverage-losing candidate leaves the last-good cache byte-for-byte unchanged. A separate `.refresh.json` attempt record exposes failure type and check time without logging secrets. Staleness and observation age are recomputed from the recorded latest attempt/current check, not reset by a failed call. The previous snapshot retains its actual common endpoint and window dates.

A review may explicitly allow a reduced candidate with `--allow-partial-regression`; it still cannot bypass date, identity, licensing, corporate-action or arithmetic validation. It is not the default. No provider-specific fetch loop or paid subscription is enabled.

Exit status is 0 for successful validated replacement and 2 for an unavailable/malformed/ineligible source. A source failure is a narrow blocker for acquiring real data; it does not turn test fixtures into a public snapshot.

## Tests

`python -m pytest tests/test_market_snapshot.py -q` covers exact return arithmetic against underlying closes, real calendar endpoint/half-day rules, month and YTD windows, trading-date omissions, future data, permissions, splits/reverse splits, dividend basis, ticker chronology, IPOs, stale/missing closes, common normalization, unexplained discontinuities, size boundaries, capitalization blockers, literal quote/index separation, secret-bearing URLs, atomic last-good preservation and regressive partial inputs. All price fixtures are explicitly synthetic and exist only inside tests.
