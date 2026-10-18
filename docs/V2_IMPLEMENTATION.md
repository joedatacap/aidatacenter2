# V2 implementation and validation

Branch: `codex/v2-financing-risk`, started on main `482d091` (merged PR #3), then integrated main `c01b04d` and its new repository instructions. Implements Issue #2 and V2_FINANCING_RISK.md. Neon connectivity is owned by the independent task; this implementation makes no Neon infrastructure or transport changes and claims no actual Neon persistence test.

## Financial behavior

- Funding: independent 12/18-month entity/purpose plans, gross uses, usable sources, gap and dated equity denominator. Base, Downside and Tight credit alter declared assumptions. Conditional/restricted availability must be explicitly established. Economic cashflow keys and inclusion links prevent debt proceeds/cash and prepayment/CFO duplication. Incomplete plans, conflicting operating flows and duplicate identities suppress a precise gap. Explicit rate-sensitive uses separate future refinancing assumptions from existing interest exposure.
- Debt cost: specific security ID, dated quote, price/yield type, source, liquidity, coupon, original yield and floating spread remain separate. Stale/media references do not become current quotes. Treasury spreads require aligned observation dates, exact maturity and evidence. No synthetic price history or invented live yield.
- Backing: project → issuer/instrument → contract → legal obligor → guarantor, with cap, period, restrictions, construction risk, concentration and merchant fields. Numeric/relationship source gates and independent audit precede live calculations. HUT project ratings are not a parent rating; Google support is limited to the lease.
- Coverage: consistent TTM EBITDA and cash interest, N/M for nonpositive EBITDA, explicit cash-interest/expense/capitalization distinctions, CFO and capex/FCF. Floating balances retain known hedge and unknown buckets; active partial hedges, forward starts, expiration and disclosed benchmark floors affect immediate shock calculations. Missing current hedge terms remain unknown.
- Principal: dated amortization/bullet/current-portion rows, deduplication identities, 12/18/24-month horizons, entity/recourse and repayment support. Annual/range buckets crossing a horizon remain unallocated, rather than acquiring invented monthly dates. A partial schedule is never a complete company debt wall.
- Secondary leverage: complete, reviewed balance snapshots can calculate gross and net debt/equity. Known partial principal totals retain incomplete labels. Negative net debt is preserved; currencies are not converted silently.

## Persistence and migration coordination

`repository.py`, `neon_http.py` and `connectivity.py` are unchanged. V2 extends the existing run JSONB contract, so memory, direct Postgres and the Neon HTTPS adapter retain the same `initialize/save/get/all/heartbeat/close` interface. Initial/final audits, parent IDs, provisional records, evidence, budgets and response checkpoints persist together with the V1 run.

Migration `002_financing_risk.sql` is additive and also appended to `schema.sql` for both existing initialization paths. It creates two read projections, a version record and a GIN index. It does not rename tables, alter V1 positional insert columns, create another database, change connection handling or run against production Neon in this task. Reapplying it is idempotent. Keep the projection and standalone migration in sync when reviewing the separate connectivity PR.

A dedicated global budget run stores conservative reservations using the same interface. One worker/lease remains required. A crash between ledger reservation and response reconciliation may overreserve estimated spend; this fails toward a lower spend allowance. In development memory, persistence and cumulative budgets reset on process restart, as labeled by health diagnostics.

## Runtime and provenance

Runtime inference uses Crusoe only. Five requested model families were discovered and tested with actual structured responses before configuring defaults. Exact account model spelling differs from the spec's display names. Discovery alone does not enable a route: JSON verification and maintained pricing are required. Role-specific overrides are supported; fallback handles unavailable models, rate limits and malformed/truncated responses. Model usage, latency and cost estimates are retained per attempt, including conservative failed-attempt reservations.

Two real comparison investigations reached a partial dossier with actual manager-selected children after GLM auditor concerns, persisted in disposable TLS Postgres. Sanitized task ancestry/telemetry appears in V2_LIVE_VERIFICATION.json. The earlier CRWV/HUT trace exposed provisional prose entering dossier context; the final implementation restricts dossiers to reviewed structured records and their evidence and adds an audit after followup. Empty/malformed specialist envelopes are rejected rather than silently treated as complete extraction.

The HUT corpus contains exact retrieved public SEC excerpts, not model-generated evidence. It distinguishes June 30 principal balances from later commitments and preserves unknown legal conditions. The issuer website was policy-blocked; its Baa2 claim was independently located in the SEC 10-Q instead. No request was made to alter that policy.

The final HUT investigation completed both GLM-5.3 audits, two real manager-selected followups and a constrained dossier: 16 tasks, 22 inference attempts, 4 source fetches, estimated $0.2587. One instrument and two annual repayment buckets received runtime audit approval; other records stayed provisional. The persisted outcome is `partially_completed`, accurately reflecting missing funding forecasts, quotes and TTM data.

## Validation

- Full Python suite: **77 tests passed**, including all V1 tests, real disposable TLS Postgres, existing HTTPS protocol bridge, idempotent migrations, V2 snapshot recovery, formulas, numerical provenance gates, route verification/fallback, budgets and API user-assumption status.
- GitHub Actions passed for implementation commit `744d934` (run 39088139269).
- Python compilation and syntax checks for both JavaScript entry points pass.
- Chromium: CRWV/HUT demo, Base/Tight credit behavior, visible source-backed HUT data, audit ancestry, refresh recovery, desktop and 390px mobile layout, no horizontal overflow and no JavaScript errors. V1 remains accessible at `/v1`. The final browser run also saved explicit user assumptions and verified the second audit in the task tree.
- All synthetic demo inputs are labeled. Actual live partial runs do not invent market capitalization, a 12/18-month forecast, TTM cash-interest denominator or a licensed bond quote when the supplied sources do not establish it.

## Remaining disclosure limits

This is a working financing-risk engine, not an assertion that every company has a complete financial dataset. The bounded primary-source catalog may not contain every quarter needed for TTM calculations, future committed capex, fresh equity capitalization, instrument prices or detailed hedge/guarantee documents. Missing inputs remain unavailable; users can enter labeled funding scenarios. Auditor decisions supplement deterministic gates and require human review for investment use. No composite safety ranking or deployment to public hosting is claimed.
