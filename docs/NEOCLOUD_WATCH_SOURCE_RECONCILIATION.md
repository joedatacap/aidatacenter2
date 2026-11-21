# Source reconciliation: audited public snapshot

Reconciled November 20, 2026. This is a source/build reconciliation, not a claim that every fact was researched again on that date.

## Reference and method

Reference checkout: `watch-public-source`, commit `d5ae5a6f8fa8d7d184d1424b4f41f39c4083be7e`. The public snapshot contains `dist/`, `maintenance/source-corrections.patch`, `maintenance/audit.html` and `maintenance/NEOCLOUD_WATCH_AUDIT.md`.

The correction patch was authored against the initial Watch implementation, while the application repository subsequently added source-linked analyst reads. Applying the patch wholesale would conflict with those additions. We reconstructed the patch's exact original Git blobs in an ignored working directory, applied the patch there, and merged its JSON changes by record identity into the current source. There were no semantic conflicts. The application repository retains its analyst-read renderer, historical interpretations and nine call-transcript sources.

The reconciled `load_snapshot()` result was compared recursively against public `dist/data.json`. After excluding only `analyst_read` objects and the nine additional call-transcript source objects, every field compares equal. The canonical financial/evidence graph (UTF-8 JSON, sorted dictionary keys, compact separators, original array order) has SHA-256:

`c0dd34f72b3f3f41a8a42493f5dc0e5fca181f9b08d166a05d5e102103b3aab2`

The public snapshot has 223 sources; the reconciled application has 232. The extra sources are the existing `call-…-20261117` transcript records, not replacements for the audited filings. All nineteen company identities and all audited quarterly metrics, derived metrics, cash/debt data, source dates, operating facts, market snapshots and scope qualifications agree with the reference.

## Corrections retained

- SharonAI Q3 September 2026 results and balance sheet replace Q2 as the latest loaded financial period. Restricted cash and certificates remain excluded from reported cash. Equipment advances remain distinct from the purchases-only cash-capex line.
- Axe Q3 September 2026 results and balance sheet replace Q2. Deferred acquisition consideration remains explicitly described; customer prepayments and leases stay separate from financing obligations. Nine-month cash flow is not presented as quarterly cash flow, and historical consolidated revenue is not silently comparable with continuing operations.
- Completed report events cannot remain the next catalyst. A model regression test covers both reported and completed event statuses, including a report dated on the review cutoff.
- IREN and Applied Digital display actual period ends alongside their fiscal-year labels; the fact that both are fiscal Q1 FY2027 does not make them January–March calendar quarters.
- The data audit is preserved in `docs/NEOCLOUD_WATCH_AUDIT.md` and as a static `audit.html` asset. Nine companies have earnings coverage; ten contextual companies retain financing references without being labelled earnings-reviewed.

## Interpretation boundary

The newly loaded SharonAI and Axe Q3 cards receive concise **release/filing-based** analyst reads, citing the audited Q3 sources. They do not claim a Q3 call transcript was reviewed. Their prior Q2 transcript reads remain attached to Q2. The interpretation review date is November 20; the financial snapshot and issuer publication dates remain November 17 and the individual source dates. Market snapshots remain November 13 or November 12 as recorded.

## Validation

`python -m pytest tests/test_watch.py -q`: 25 passed after reconciliation. The tests cover the corrected latest periods, obligations and cash balances, deferred consideration, separate prepayments/leases, absent quarterly Axe cash flow, original financing preservation, original-period transcript association and completed-event exclusion. Full browser, packaging and deployment validation are recorded separately by the coordinating task.
