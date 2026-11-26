# Equity source coverage

Audit date: 2026-11-26. Cohort: CRWV, NBIS, IREN, APLD, HUT, WULF, WYFI, SHAZ, AGPU. Coverage describes repository evidence, not a live-data service or completed independent audit.

## What exists

The source of reviewed equity work is `neocloud/data/equity/*.json`; older `website_v2.json`, `debt_directory.json`, `watch_smaller.json` and three terminal profiles remain useful dated evidence, not interchangeable current financial statements. Models are analyst assumptions, not consensus. A present JSON file does not mean its forecast is validated or its market-data redistribution authorized.

| Company | Landed forward coverage at final check | Primary financial evidence available | Highest-value reconciliation |
|---|---|---|---|
| CRWV | Six scenarios; gross profit withheld | [September 30 10-Q](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000465/crwv-20260930.htm) | Debt principal/carrying, customer cash versus delivery uses, GPU replacement and dilution |
| NBIS | Six scenarios, all six metrics numerically modeled | [September 30 detailed statements](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126238/nbis-ex99d2.htm) | Prefunded warrants; $28M debt-table discrepancy; post-quarter financing |
| IREN | Six scenarios; FCF withheld | [September 30 10-Q](https://www.sec.gov/Archives/edgar/data/1878848/000187884826000066/iren-20260930.htm) | GPU financing and acceptance; calendar-year versus June fiscal-year forecasts |
| APLD | Six contract-bridge scenario slots; consolidated metrics withheld | [August 31 10-Q](https://www.sec.gov/Archives/edgar/data/1144879/000114487926000059/apld-20260831.htm) | Project preferred waterfall and parent cash access; book minority value is insufficient |
| HUT | Six contract-bridge scenario slots; consolidated metrics withheld | [September 30 10-Q](https://www.sec.gov/Archives/edgar/data/1964789/000119312526446146/hut-20260930.htm) | Mining/subsidiary interests versus AI projects; guarantees and project recourse |
| WULF | Six contract-bridge scenario slots; consolidated metrics withheld | [September 30 10-Q](https://www.sec.gov/Archives/edgar/data/1083301/000162828026071671/wulf-20260930.htm) | Project ownership, tenant acceptance, lease revenue and construction funding |
| WYFI | Six contract-bridge scenario slots; consolidated metrics withheld | [Issuer hub links Q3 release and 10-Q](https://www.whitefiber.com/investors) | GPU-cloud versus colocation economics; parent ownership; existing provider P/S mismatch |
| SHAZ | Six contract-bridge scenario slots; consolidated metrics withheld | [November 16 Q3 release](https://www.sec.gov/Archives/edgar/data/2068385/000149315226052409/ex99-1.htm) | Class A+B and financing dilution; commissioned versus accepted/billing capacity |
| AGPU | Six scenario slots; consolidated metrics withheld; components provided | [September 30 10-Q](https://www.sec.gov/Archives/edgar/data/1446159/000117184326007507/agpu20260930_10q.htm) | Prefunded economics; Georgia amended contract; acceptance and customer-funded cash |

Final filesystem check: all nine equity JSON files have landed, each with six year/scenario slots. Only NBIS supplies all six numerical metrics in all six scenarios; these remain explicit analyst assumptions, not superior evidence quality. CRWV withholds gross profit and IREN withholds FCF. The other six records carry components/contract bridges while withholding unsupported consolidated forecasts. Do not market 54 scenario slots as 54 completed six-metric models. All nine have public financial evidence; rerun the inventory at release.

## Required inputs versus derived results

| Layer | Required source inputs | Derived output | Legitimate reason to withhold |
|---|---|---|---|
| Market equity | Quote/session/currency; dated A+B/common; nominal prefunded warrants; treasury exclusion | Price × defined economic shares | Current share bridge or quote rights unresolved; vendor market cap alone insufficient |
| Enterprise value | Same-date debt basis; cash restrictions; preferred; minority claim; lease convention | Equity + debt + preferred + minority − eligible cash | Unresolved instrument/dates or filing contradiction; still show qualified historical alternatives |
| TTM | Latest annual + current YTD − prior matching YTD, continuing-operation scope | Revenue, EBITDA, net income, operating cash less capex | Missing quarter is a retrieval task first; actual reclassification/definition conflict may block |
| Earnings models | Delivered/billed capacity, yield, utilization, cash costs, GPU cohorts/lives, debt cost, tax | Six 2027/28 metrics with reproducible assumptions | Forward inputs undisclosed: scenario ranges, not fabricated guidance |
| Funding | Opening accessible cash, expected collections, facility draw conditions, capex payments, maturities, minimum liquidity | Dated 12/24-month funding gap | Commitment ≠ draw; prepayments cannot fund construction twice |
| Research performance | Immutable publication time, corporate actions, licensed adjusted closes for stock/benchmarks on identical sessions | Prospective price return/excess return | No public release timestamp, missing required session or data rights |

Missing must be labeled **not yet retrieved**, **available but not reconciled**, **not disclosed**, **future assumption**, or **rights not established**. Never substitute zero. Excluded antidilutive shares are not zero economic dilution. Never retain a converted debt claim and add the same conversion shares. ARR, total contract value and annual recognized revenue remain separate.

## NBIS specific resolution

September 30 balance sheet and Note 14 describe ordinary A/B/C capital only; issuer preferred is recorded as a **dated zero**, not an assertion about future issuance. Toloka preferred stock is an investment asset. Add $1M book minority interest only as an explicit proxy. Nominal NVIDIA prefunded warrants bring the dated minimum economic denominator to 313.968341M; treasury and already-issued ATM shares are not added again.

At the November 25 $84.99 closing observation, two qualified, mixed-date EV references are $33,450.369M using balance-sheet carrying debt and $33,422.369M using Note 12 carrying debt. Both include preferred zero, book minority $1M and exclude restricted cash; neither is a clean current EV. The same filing reports $187.5M current debt on its balance sheet versus $159.5M in Note 12, a $28M difference requiring reconciliation. Future accreted principal is not silently substituted for current debt value. October Citi draws, subsequent cash/share movements and minority market value remain separate limitations. [Detailed filing](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126238/nbis-ex99d2.htm)

## Storage and publication boundary

The lead verified zero database bindings on the hosted Site. A separate read-only catalog in `aidcneon` / `aidc_copy_20261111` contains 40 tables/views, including `financial_measures`, `claims`, `source_documents` and `publication_manifests`. No records were exported and no authorization to distribute those records through this app is established. Schema discovery is not a live connection, provenance review or publication entitlement. Existing repository JSON remains the release input; credentials and private records must not enter static assets.

## Source and benchmark rights

[SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) provide public submissions/XBRL without an API key; custom tags and contract footnotes still require filing review. SEC does not support browser CORS, so intake belongs in a controlled build/review pipeline. Public access is not permission to reproduce complete third-party narratives: store factual extracts, short attributed passages and original links.

[Stock Analysis terms](https://stockanalysis.com/terms-of-use/) allow attributed snippets but restrict automated access and prohibit using its data/content to build a competing product/database. Its AI-crawler exception is not a production redistribution license. Existing dated research observations do not establish rights to an automated market feed or benchmark history. Obtain an expressly authorized source before recurring ingestion/public redistribution; a paid subscription alone does not prove those rights.

Benchmark scoring currently specifies **QQQ, NVDA and a frozen equal-weight peer cohort**, not the Nasdaq-100 index. QQQ is an ETF price-return proxy; do not call it the index or total return. The same rights, adjustment basis, sessions and currency must apply to stock and benchmarks. `scripts/equity_history.py` implements prospective records/pending states and accepts reviewed observations; it is not a licensed downloader or evidence that history has been supplied. Returns exclude dividends, fees and slippage unless that methodology is deliberately changed for every series.
