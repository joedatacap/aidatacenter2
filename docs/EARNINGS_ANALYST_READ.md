# Earnings analyst reads — November 17, 2026

Earnings report cards now open with **Analyst read**, containing one to three source-linked bullets. Each bullet identifies what matters, what changed or what to watch, with interpretation kept distinct from management's statements.

The latest **covered** quarter of all nine focus companies has a reviewed call transcript:16 bullets across nine calls. Each of the23 older quarters has a release/filing-based interpretation and explicitly states that its call transcript has not been reviewed. Missing call review is not silently filled with release commentary labelled as a call insight.

| Company | Covered financial period | Actual call date | Transcript publisher |
| --- | --- | --- | --- |
| CoreWeave | Q3 2026 | 2026-11-10 | Issuer proofread transcript PDF |
| Nebius | Q3 2026 | 2026-11-12 | Stock Analysis / Quartr |
| IREN | Q1 FY2027 | 2026-11-05 | Stock Analysis / Quartr |
| Applied Digital | Q1 FY2027 | 2026-10-07 | Stock Analysis / Quartr |
| Hut 8 | Q3 2026 | 2026-11-04 | Stock Analysis / Quartr |
| TeraWulf | Q3 2026 | 2026-11-06 | Benzinga full transcript |
| WhiteFiber | Q3 2026 | 2026-11-10 | Stock Analysis / Quartr |
| SharonAI | Q2 2026 | 2026-08-06 | Roic AI |
| Axe Compute | Q2 2026 | 2026-08-17 | Stock Analysis / Quartr |

Call dates and financial release dates are separate. Axe's Q2 call occurred August17; its financial release was August14. Transcript review on November17 does **not** refresh the financial snapshot dated November16 or promote newly discovered SHAZ/AGPU Q3 results. Refreshing those financial quarters remains the follow-up identified in the existing handoff.

The section appears on Earnings > Results/History and the company's Earnings section, changing with the selected fiscal period. It is included in existing JSON/CSV exports through each quarter's `analyst_read` object. Source drawers show transcript URLs, publication/retrieval dates and supporting passages. The source ledger adds nine transcript records; existing financial observations remain unchanged.

The builder validates one to three nonempty concise bullets, linked sources, call/release basis, call chronology, and transcript identity matching the company, financial period and call date. A filing source cannot masquerade as a reviewed call. Source text is escaped by the existing renderer.

Maintenance: review the actual public transcript, add its short supporting excerpts and source metadata, then update only the corresponding quarter's `analyst_read`. Do not carry a later call's conclusions into an earlier period. Run `python -m pytest tests/test_watch.py -q` and `npm run test:watch`, rebuild the snapshot, and update the review artifact. Historical transcript coverage can expand incrementally without changing the financial figures.
