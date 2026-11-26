# Prospective research accountability

`versions/{company}/{sha256}.json` freezes the full research content and peer membership at first archive observation. The hash covers the content; recording timestamps are kept in the immutable Git record. Re-running unchanged reports does not change that timestamp. Investment packages preserve all source definitions and remain previews until explicitly released. Research `as_of` dates never prove publication.

`release-notices/{version_id}.json` records an explicit public URL, publication timestamp and notice-recording timestamp. The three original Justin reports were published on November 26, 2026 at 05:43:17.065908 UTC; their notices preserve that deployment evidence. Performance entry nevertheless starts after archive/notice capture, never retrospectively at a favorable older quote. Future investment releases require explicit notices through `register_release` or `--release-manifest`.

`scorecard-runs/` and `event-runs/` are immutable observations, including incomplete coverage. Old previews remain internal audit records; only released versions should appear as published track records. No script overwrites earlier records or promotes a preview to a public recommendation.

## Scoring contract

`build_scorecard(history_dir, observations, as_of=None)` returns versions, 1w/1m/3m/6m/12m calendar horizons and freshness. An observation export maps uppercase symbols to arrays of `{date, close, source_url, retrieved_at, basis, currency}`. Dates use ISO; timestamps require a timezone; currency must be USD. Basis is `raw_close` or `split_adjusted_close`, and only the latter scores. Provider source and retrieval times travel with scored entry and exit values.

Entry and exit must match the expected regular NYSE session exactly. The calendar handles ordinary exchange holidays including Good Friday; it cannot infer an emergency closure. Missing expected sessions keep results pending rather than shifting the entry or exit. Equity delistings require reviewed economic proceeds/corporate-action treatment; absent prices are not zero or a fabricated win. No forward-filled price or survivor substitution is allowed.

Benchmark returns use identical sessions for QQQ, NVDA and the frozen equal-weight peer basket excluding the subject. Every peer is required. Returns describe the underlying stock, not a simulated buy/short trade, execution result, total return including dividends, or directional rating win rate. A Sell rating is not silently scored as a short position. Six/twelve-month observations do not retroactively lengthen a stated 30–90-day tactical objective.

The initial observations reuse dated raw research quotes. There is no authenticated/approved automated split-adjusted price feed connected. QQQ/NVDA and future prices remain missing; scheduling the workflow does not solve that missing-data dependency. Supply a reviewed/licensed observation export explicitly with `--observations`. No new paid service is activated.

## Event coverage and persistence

`scan_equity()` reuses the existing SEC/issuer scanner for nine issuer CIKs, all recent SEC filing forms, issuer news indexes and six additional event/presentation indexes. It validates CIK identity and applies the existing bounded, rate-limited HTTPS fetcher, identifying User-Agent and same-origin redirect rule. Empty/dynamic listings, blocked hosts and unparsed assets remain per-source errors. Discovery is not document-content verification. Transcript ingestion, complete exhibit extraction and cross-origin slide text remain explicit gaps.

`build_events(queue, reports, previous=None)` deduplicates SEC accessions and canonical issuer URLs, retaining separate documents/exhibits, first-seen timestamps, report-version hashes, observed revisions, prior dispositions and unresolved gaps. Title/form keyword matches generate review questions only; `impact` stays `unassessed`. Source failure cannot produce an all-clear. The optional `--queue` supplies a saved intake; otherwise the nine-issuer scan runs live.

The scheduled workflow emits review artifacts and persists **additions only** on `equity-monitor-history`, independent of 90-day artifact retention. It never force-pushes and rejects staged modifications/deletions. Only the history directory is staged. The application/default branch, published research, deployments, messages and brokerage orders are untouched. Branch protections or token restrictions may block persistence; the job then fails visibly and still uploads its artifact. No branch has been created by local execution; persistence starts when the workflow is merged and run with repository permission.
