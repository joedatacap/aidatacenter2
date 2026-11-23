# Company-size observation review — November 24, 2026 (Singapore)

Checked at **2026-11-23 18:02:19 UTC** (**November 24, 02:02 Singapore**).
This was one bounded editorial review of the nine public capitalization pages, using the narrow attributed-snippet policy in [WATCH_MARKET_SOURCES.md](WATCH_MARKET_SOURCES.md). No price-history feed, bulk download, or market-data export was added.

## Session and date decision

The November 23 US equity session was still open: 13:02 EST, before its normal 16:00 EST close. The last completed session was **Friday, November 20, 2026, at 21:00 UTC**. See the [NYSE calendar](https://www.nyse.com/trade/hours-calendars) and the completed-session evidence in the source audit.

Every company's capitalization heading explicitly dates the capitalization itself to **November 23**, with a new amount. These qualify as **provider-reported intraday observations**, not November 23 closes. The source pages' price headers say “Market open”; their times vary and must not be assigned to the cap. Each cap has date precision only.

All nine pages also retain **“Last updated: Nov 20, 2026”** in their data-source metadata. That conflict remains explicit in every observation's discrepancy. The dated heading supports the limited editorial observation; it does not establish independently reconciled shares, a live feed, or a completed-session value.

## Per-company observations

Only the short cap excerpt is quoted below; the words and amounts remain as displayed by the individual source page.

| Ticker | Exact capitalization excerpt | Observation status | Size band |
| --- | --- | --- | --- |
| [CRWV](https://stockanalysis.com/stocks/crwv/market-cap/) | “$26.99 billion as of November 23, 2026” | Intraday; date only | Large |
| [NBIS](https://stockanalysis.com/stocks/nbis/market-cap/) | “$29.33 billion as of November 23, 2026” | Intraday; date only | Large |
| [IREN](https://stockanalysis.com/stocks/iren/market-cap/) | “$6.36 billion as of November 23, 2026” | Intraday; date only | Mid |
| [APLD](https://stockanalysis.com/stocks/apld/market-cap/) | “$4.22 billion as of November 23, 2026” | Intraday; date only | Mid |
| [HUT](https://stockanalysis.com/stocks/hut/market-cap/) | “$6.43 billion as of November 23, 2026” | Intraday; date only | Mid |
| [WULF](https://stockanalysis.com/stocks/wulf/market-cap/) | “$5.64 billion as of November 23, 2026” | Intraday; date only | Mid |
| [WYFI](https://stockanalysis.com/stocks/wyfi/market-cap/) | “$347.81 million as of November 23, 2026” | Intraday; date only | Small |
| [SHAZ](https://stockanalysis.com/stocks/shaz/market-cap/) | “$794 million as of November 23, 2026” | Intraday; date only | Small |
| [AGPU](https://stockanalysis.com/stocks/agpu/market-cap/) | “$79.4 million as of November 23, 2026” | Intraday; share basis unresolved | Micro |

No row relies solely on a newly dated stock-price header. All nine have new cap-specific dated headings. No new completed-session cap was verified, and none is claimed. The November 20 observations are historical relative to these intraday observations, but remain the latest reviewed completed-session observations.

## Reconciliation and preservation

- **WhiteFiber:** the intraday cap moves back above the $300M boundary, making the current observed band Small. Its November 20 Micro observation is preserved; this is an intraday change, not a new close.
- **Axe Compute:** the November 23 headline and the November 20 history row now have different dates. They must not be described as a same-date conflict. Its earlier November 20 headline/history conflict, share-count uncertainty and prefunded-warrant scope remain documented; the historical debt ratio stays withheld.
- **Nebius and SharonAI:** primary share-class and prefunded-warrant passages remain attached. Updating a provider cap does not bridge all subsequent issuance or clear the historical debt-ratio restrictions.
- All primary share-source URLs and supporting passages were preserved unchanged. They retain their original filing/count dates; this task does not claim to have refreshed financial statements or reconciled shares to November 23.

The complete prior November 20 observations, snippets, discrepancies and primary passages are permanently preserved in [quality_sizes.json at commit 39c82c4](https://github.com/joedatacap/aidatacenter2/blob/39c82c43ffd0861331c071ac4c965f18b420a916/neocloud/data/quality_sizes.json). The November 13 baseline in `watch_markets.json` also remains unchanged. No duplicate vendor archive was created.

## Data fields and verification

`quality_sizes.json` retains `status: "provider_reported"`, with optional `session_status: "intraday"`, `time_precision: "date"`, and `metadata_last_updated: "2026-11-20"`. The quality overlay validates and passes these fields through. `qualification_label` is reserved for Axe Compute's company-specific unresolved share basis; the common intraday status belongs in the comparison's shared context.

Targeted data-quality tests cover preservation of session context, optional labels, metadata chronology, invalid statuses and retention of the underlying debt-ratio restrictions. Financial calculations and the historical market-cap ledger were not changed.

Validation: `work/v2-venv/bin/python -m pytest -q tests/test_data_quality.py` — **32 passed**. `git diff --check` also passed for the changes at review.

A later review after the actual US close must obtain newly dated source evidence before claiming a November 23 completed-session observation. Merely passing 21:00 UTC, or reading an unchanged page, is insufficient.

