# Website V2 evidence and release boundaries

Snapshot review: November 12, 2026. Retrieval completed November 13 UTC (November 12 US Eastern). This is an offline, dated research product, not live market data. The new website uses `neocloud/data/website_v2.json`; `neocloud/website_v2.py` validates and enriches a copy of the existing directory. Original calculations, source ledger and backend schemas remain unchanged.

## Market valuation policy

All 15 listed records have a USD company-market-cap observation from their Stock Analysis market-cap page dated November 12. These are rounded, provider-reported values. The page's daily observation is recorded; we do not invent an intraday fixing time or reconstruct market caps from rounded prices. Different vendors, share-class treatment and update times can produce different values. No automated refresh, subscription or license purchase is included.

Indicative debt/market-cap uses the reported borrowing carrying amount (all leases excluded) divided by that equity value. It is not book debt/equity, enterprise value, default probability or a pro-forma current balance sheet. Both observation dates remain visible. Subsequent corporate actions are not silently added to the numerator. The CSV preserves the definition, vendor status, dates and qualifications.

Nebius's ratio is withheld: the Q3 release reports 292,902,405 outstanding A+B shares, while the vendor's $35.26B capitalization does not reconcile with that share count and its $128.64 closing quote. This does not prove the vendor is wrong; timing and methodology need reconciliation. Galaxy's borrowing numerator remains unresolved. Nscale's November 12 amended registration statement still describes an IPO application under proposed NYSE symbol NSCL; the internal NSCALE record is not a listed-equity valuation.

Large means at least $10B; mid means $2B to below $10B; small means below $2B, based on these snapshots. The current 15-public-company universe has four large, nine mid and two small companies. It does not meet a five-to-six small-public-neocloud quota; no private firms or unrelated tiny stocks are inserted to create one.

## Financial refresh and debt detail

Nebius's Q3 balance sheet supersedes its old Q2 snapshot in this website only: $187.5M current debt plus $14,003.3M non-current debt; $7,425.6M cash and equivalents; $38,744.1M assets. Older note, lease and facility evidence retains its original dates. The old derived book-leverage field is removed from the enriched snapshot to prevent a stale ratio in JSON exports. The Q3 cash definition does not inherit Q2 restricted-cash amounts.

CoreWeave's September 30 note 10 provides 19 populated principal rows, including aggregated OEM/software arrangements and USD-equivalent EUR notes. They total $47.505B, versus $46.873B carrying debt after $632M of discounts and issuance costs. The issuer's repayment schedule reconciles to principal: remaining 2026 $2.433B, 2027 $10.974B, 2028 $5.479B, 2029 $4.727B, 2030 $4.247B, thereafter $19.645B. Annual buckets cannot establish exact rolling 12/24/36-month totals. Effective accounting rates are not cash coupons.

Hut 8 has four selected September principal rows with recourse labels and contractual maturity dates. River Bend's Google lease backstop does not guarantee the project notes or Hut 8 corporate debt. Final maturity is not an amortization schedule. Other companies retain sourced borrowing components, financing-rate references and historical note examples; complete instrument inventories and rolling repayments remain gaps. No artificial zero repayment totals are shown.

## Operating coverage

| Company | New context | Remaining limitation |
| --- | --- | --- |
| CoreWeave | Anonymous customer concentration; backlog; active/contracted power; named production hardware; quarterly revenue | Customer identities not inferred from A/B labels; no fleet-wide model counts |
| Nebius | Prepayment coverage of signed contract value; named customers; four revenue-producing sites; hardware integration; Q3 revenue | No top-customer revenue percentage or consolidated live MW in this extract; vendor share reconciliation pending |
| IREN | Top-three revenue concentration; Microsoft term/value and delivery conditions; accepted Horizon 1 IT load and GB300; segment revenue | One deployment is not total operating capacity; contract value is not current revenue |
| Bitdeer | AI backlog; A102 commitments; live A101 versus secured pipeline; deployed GPU count/models; segment revenue | Mixed Bitcoin/AI business; future deliveries and model-level counts incomplete |
| Hut 8 | Fluidstack/Google project scope; restricted construction accounts; project principal inventory | GPU ownership unknown; no full repayment schedule |
| HIVE | Enterprise and Bell/Cohere contracts; deposit; live versus contracted ARR; deployed B200 and planned GB300; segment revenue | ARR is not recognized revenue or MW; planned hardware not assumed operating |
| Applied Digital | Customer concentration; contracted critical IT load and Delta Forge 2 construction | Anonymous customers; consolidated live capacity/GPU ownership not established |
| Core Scientific | Colocation concentration; AMD contract duration and future delivery | AMD leases had not commenced at the snapshot; tenant GPUs not attributed to issuer |
| Cipher | Fluidstack tenant; phased Black Pearl delivery versus construction projects | Site power rating does not prove accepted HPC IT capacity |
| TeraWulf | HPC customer count; energized critical IT load; JV sale agreement | Customer count is not consolidated concentration; GPU fleet not established |
| Galaxy, Riot, MARA, Equinix, Digital Realty | Existing dated debt/cash evidence plus provider valuation | New contract, GPU and operating-capacity research not completed; retained as context peers |
| Nscale | IPO application status | Private reference; later debt and operating refresh still needed |

## How to maintain this release

1. Read the issuer filing or release; add a unique source URL, title, publication date, retrieval date and short excerpt. Retain scope and dates on each fact. Curated facts are summaries, not a full filing extraction.
2. Classify capacity as operating, commissioning, contracted, construction or announced. Never aggregate different statuses or mix power MW with IT MW, GPU counts or ARR.
3. Add new valuation observations with their provider status and any ratio blocker. Use a new dated snapshot; do not silently relabel an old one as current.
4. Run `npm run build:v2`, `python -m pytest tests/test_website_v2.py`, and `npm run test:v2`. The build rejects unresolved sources, unsafe URLs, future fact dates, private public-market valuations, invalid amounts and schedules that fail to reconcile.
5. Review desktop/mobile screens, filtered CSV/JSON, missing-data labels and company routes. Upload the standalone HTML to the app folder; record commit and CI status in the plan.

The V3 backlog remains funding-gap scenarios, hedge-adjusted interest stress, covenants, conversion/dilution, live alerts and automated research. There is no new hosting or database dependency for this release.
