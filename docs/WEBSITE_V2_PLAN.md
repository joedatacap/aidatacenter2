# NeoCloud — V2 Product Plan and V3 Roadmap

Product direction • November 12, 2026 • Working plan

## 1. Purpose and decisions

Help a stock analyst and a neocloud employee understand who owes money, what financing costs, when obligations fall due, and which customers and assets support repayment. V2 is a fresh product design: the old website’s layout, tabs, rankings and three-company comparison limit do not constrain it. Reuse sound evidence and tested calculations, not its information architecture. This chat is the primary project conversation. This Drive folder holds product plans and review previews; GitHub remains the code and data record.

The core experience is an analyst workspace spanning the company universe, with a detailed company brief. Debt structure is the centerpiece. Valuation, customer quality and revenue-producing infrastructure provide context. No composite health score or investment recommendation is inferred. Cloudflare, custom domains and Neon troubleshooting are outside the current work.

## 2. V2 scope: three questions

### What are the financing obligations?

Show reported borrowing carrying value and contractual principal separately. An instrument inventory records borrower, outstanding balance and date, facility commitment and drawn amount when known, currency, instrument type, fixed coupon or floating benchmark/spread, maturity and precision, collateral, parent/project recourse, guarantees, conversion terms and hedges. Separate lease obligations and customer financing from conventional borrowings. Historical note examples must never masquerade as a complete current debt stack.

Show cash and its restrictions alongside financing. Group cash is not automatically spendable parent cash. Selected facilities do not establish total credit availability. Never add cash, conditional commitments and letters-of-credit headroom into a misleading liquidity total. Use principal, not accounting carrying value, for repayment schedules. Display 12/24/36-month maturities only when amounts and dates are supported; incomplete schedules retain an explicit coverage label.

### What does the equity valuation imply?

The essential valuation fields are dated market capitalization and borrowing debt / market cap. Start with verified consolidated equity capitalization in the same currency as debt. The numerator is explicitly named: reported borrowing carrying value, leases excluded. Display financial-statement date, market-data observation time, currency, source, and any material intervening issuance/repayment. This ratio is not debt/equity book value, enterprise value, repayment capacity or default risk.

Add revenue and comparable-period growth when sourced. Avoid unnecessary multiple panels in the first release. EV/revenue, EV/EBITDA, net leverage and convertible dilution belong in a later phase unless the underlying coverage is complete and definitions are comparable. Private financing-round valuations are not stock-market capitalizations and cannot enter the same ranking. No market-cap figures are invented for the prototype.

### What supports future revenue and repayment?

Contracts: major customers, top-customer/top-three concentration where disclosed, period and revenue denominator, contract duration, minimum commitments, termination conditions, prepayments, legal obligor and guarantee scope. Backlog remains distinct from recognized revenue and guaranteed cash. A project guarantee is not a company-wide guarantee.

Capacity: distinguish energized/operating, contracted, under construction and announced capacity; show units, dates, ownership and project scope. MW of utility power, IT load, GPU count and annual revenue are not interchangeable. Operating capacity does not establish utilization. GPUs: disclosed generation/model mix, counts where available, ownership versus lease, deployment dates and refresh obligations. Do not infer a representative fleet from a named deployment.

## 3. Company coverage

Start by assessing the 16 existing records, not by enforcing a quota or accepting all as equivalent neoclouds. The ledger currently classifies 15 as public and Nscale as a private IPO applicant; refresh listing status before making current valuation claims. Public-equity analysis is the default. Keep private operators in a distinct industry-reference view only when their disclosed financing is useful.

Separate GPU clouds, AI infrastructure/transition businesses, miners and data-center REITs. Select major benchmarks and medium/smaller public peers after verifying listing status, comparable market-cap dates and meaningful AI exposure. Existing candidates include CoreWeave, Nebius, IREN, Hut 8, Applied Digital, Core Scientific, TeraWulf, Cipher, Bitdeer and HIVE; these are a research universe, not a verified size ranking. Retain other existing companies as contextual peers where appropriate.

The suggested private operators—Crusoe, Lambda, Vultr, RunPod, TensorWave, Voltage Park, Ori, Cudo Compute and others—are not automatic additions to public-stock coverage. Check current ownership/listing independently. Unknown valuation means unclassified, not small. Target roughly 5 reference, 5 medium and 5–6 smaller public names only if suitable evidence supports those cohorts; otherwise report the coverage gap.

## 4. Product design

Universe workspace: a compact, searchable, sortable table with company/business type, debt, reported cash, market cap, debt/market cap, dated rate coverage and evidence freshness. Public/private and business-model filters are explicit. Unknown financial values remain unknown and sort after known values. Avoid an oversized introductory hero: the working information should be visible immediately.

Company brief: clicking a company opens a full-width, navigable brief with financing facts, instrument inventory, cash/facility restrictions, valuation basis, customers/contracts, capacity/GPUs, and sources. Distinguish missing research from a confirmed absence of debt, customers or assets. Label source date and completeness close to the number. Favor factual takeaways over traffic-light health judgments.

Comparison is optional and not capped by the former three-company design. The universe is the primary comparison surface. Later column selection and saved peer sets can add flexibility without creating a second calculation engine. Desktop supports dense analysis; mobile uses readable stacked company cards and horizontally scrollable detail tables.

Visual direction: restrained analyst terminal meets readable financial publication. Clear typography, compact navigation, subdued colors, strong hierarchy, visible units/dates and expandable source excerpts. The first preview explores a new design rather than reskinning V1. Deliver a standalone interactive HTML for easy offline review in addition to the repository preview.

## 5. Evidence and calculation contract

Each material fact has a value or explicit unknown, units/currency, entity/scope, effective date, publication date, source URL, supporting excerpt and review status. Distinguish missing, not applicable, historical and verified current-at-snapshot. Financial coverage is separate from interface completion. Existing source records are reusable historical evidence, not fresh verification.

Never compute a company-wide weighted interest rate from selected instruments. When a complete usable inventory exists, state whether weighting uses principal, how fees/hedges and floating fixings are handled, and the share covered. Coupon, market yield, accounting effective rate and future refinancing assumption stay separate. No hidden assumptions, automatic currency conversion or silent date blending.

## 6. Delivery sequence and acceptance

### Milestone A — new workspace and debt brief

Build an independent V2 static workspace using the existing curated ledger as dated evidence. Include search, public/private and business-model filters, company selection, debt and cash facts, typed financing references, note maturity detail, facility restrictions and linked excerpts. Provide an offline HTML preview. Explicitly identify valuation, contract and infrastructure research not yet populated. Do not count empty panels as completed financial coverage.

Acceptance: all retained records are reachable; filters and sorting preserve unknowns; no fabricated values; note examples cannot become a complete debt stack; cash restrictions and date differences remain visible; keyboard/mobile interaction works; standalone preview runs without API calls. This is the first implementation slice, not the complete V2 release.

### Milestone B — verified valuation and priority debt enrichment

Choose a reproducible market-cap source and observation policy without taking on unapproved fees. Validate share classes, currency and timestamps. Populate debt/market cap for eligible public companies. Prioritize a small benchmark cohort for contractual principal, current instrument balances, maturity schedules, security and recourse, then extend by evidence availability. Reconcile later corporate actions before presenting current valuation comparisons.

### Milestone C — customer and infrastructure context

Research concentration, contract terms, operating capacity and GPU disclosures for the benchmark cohort, then expand. Every numeric concentration has a period/denominator; every capacity number has units and status; every hardware claim has scope/date. Verify that comparisons do not mix backlog with revenue or announced projects with operating infrastructure. Recheck public-company coverage and show remaining gaps.

### Milestone D — usable V2 release

Review the prototype with Joe, simplify unnecessary columns/panels, complete the agreed core cohort, and add focused financial and browser regression checks. Verify source links, exports, null handling, accessible navigation and desktop/mobile layouts. Record actual tests and remaining coverage gaps in the plan. Commit work on a feature branch and open a reviewable PR; do not merge or deploy as part of this planning/start task.

## 7. Possible V3

Funding and refinancing scenarios: 12/18/24-month sources-and-uses plans, committed capex versus discretionary expansion, cash runway, parent/project cash restrictions, and scenario funding gap relative to equity capitalization. Show ranges and assumptions rather than false precision.

Advanced debt analytics: cash-interest coverage, net debt/EBITDA where meaningful, hedge-aware rate shocks, refinancing spread shocks, covenant headroom, lease-adjusted obligations and convertible dilution scenarios. Align customer contract expiry, GPU refresh requirements and debt maturity timelines.

Operating and valuation depth: EV/revenue and EV/EBITDA with consistent definitions, realized GPU economics where disclosed, utilization, customer credit quality, and revenue sensitivity to delivery delays. Avoid combining mixed-business segments into a fictitious pure-GPU valuation.

Workflow improvements: quarter-to-quarter changes, source updates and watchlist alerts, saved peer groups, richer exports, research assistance and user-authored assumptions. Automated research, authentication, paid/live market data and persistent user accounts require separate design and authorization. No composite safety score without an explicit transparent methodology.

## 8. Working status and references

Status at plan creation: GitHub main is merge 2ca6968; PR #7 and post-merge CI were verified successful. V2 implementation is starting on feat/neocloud-v2-workbench. Historical backend modules named V2 are reusable components, not proof this new website release is complete. No new valuation, contract or infrastructure facts have been verified for this release yet.

Repository: https://github.com/joedatacap/aidatacenter2
App folder: https://drive.google.com/drive/folders/1zQMWHiQuiVG5JYRUQPWw5dW4yBgMB-qT
Existing evidence methodology: https://github.com/joedatacap/aidatacenter2/blob/main/docs/DEBT_DIRECTORY.md
Post-merge baseline checks: https://github.com/joedatacap/aidatacenter2/actions/runs/43327640667

Plan document: https://docs.google.com/document/d/1ejfe4qo5nLJMwGOCclzTo9IqmRscHcrG0Spu6HkM-MU/edit

## First implementation receipt — November 12, 2026

Milestone A has a working first slice: a new company universe, search/business-model/public-private filters, sorting, deep-linked financing briefs, borrowing components, principal reconciliations, separate leases, typed financing terms, historical note maturities, liquidity conditions and source excerpts. The existing ledger supplies 15 public records plus one optional private reference; listing status has not been independently refreshed in this slice.

The standalone HTML contains its data and assets. Download and open it in a browser; Google Drive's file viewer does not execute the interactive app.

- Interactive preview: https://drive.google.com/file/d/1kko3A90R_Djzm49C1UmkKUiV77QGpG1b/view
- Screenshot: https://drive.google.com/file/d/15FdmpJhuqbifR4MY41zVQFtWWl3zcB12/view
- Branch: feat/neocloud-v2-workbench
- Validation: 16 new desktop/mobile browser checks and all 76 existing browser checks passed. Python: 131 passed; three database tests skipped because no disposable database was configured locally. CI retains its disposable TLS Postgres checks.

Next: verify dated market-cap observations and listing status, implement debt/market-cap with provenance, and enrich the company briefs with customer concentration, contract terms, operating capacity and GPU disclosures. Those fields remain explicitly unresearched in this preview. Full V2 is not complete. No deployment or live database verification is claimed.

## V2 implementation expansion — November 12, 2026

The website now implements the core V2 workflow: financing/valuation and customer/infrastructure comparison views, equity-size filters, detailed briefs, dated provider market caps, indicative debt/market-cap, current disclosed instrument tables, an issuer repayment chart, source links, filtered CSV/evidence JSON, printing and responsive mobile cards. All 16 records remain accessible; no three-company limit applies.

Financial coverage is intentionally explicit: 15 provider-reported market caps, 13 indicative ratios (Nebius withheld for share-count reconciliation; Galaxy lacks a resolved debt numerator), ten company contract profiles, five company revenue profiles, a complete reported annual principal schedule for CoreWeave and selected current Hut 8 instruments. The detailed coverage and refresh rules are in [WEBSITE_V2_RESEARCH.md](WEBSITE_V2_RESEARCH.md). Nebius Q3 financials are updated in this website without changing the original directory.

Milestones A and the core interface/exports portion of D are implemented. B and C have substantial sourced coverage but remain partial research: fully reconciled vendor share classes, every-company instrument/amortization inventories, every-company operating disclosures and an expanded small-public-neocloud cohort are not claimed complete. The current universe contains only two sub-$2B public companies at the selected snapshot. The next useful work is focused evidence completion, not more UI panels. Cloudflare, domain publishing, Neon and V3 remain outside this release.

PR: https://github.com/joedatacap/aidatacenter2/pull/8
The Drive preview link above is updated in place for this release.

Local validation for the expanded release: 146 Python tests passed with three database tests skipped locally; all 28 V2 desktop/mobile browser checks passed, including every company route, filtered downloads, principal reconciliation, unknown inputs and offline HTML. The final branch CI supplies disposable TLS Postgres and the existing 76-browser-check regression suite. CI outcome is recorded in PR #8 and the Drive plan once available.

## November 14 continuation

Added a debt repayment comparison view and three more issuer schedules: IREN, Hut 8 and TeraWulf. Four companies now have sourced annual debt schedules. Fiscal/calendar periods and each schedule’s scope remain explicit; exact rolling totals are not inferred. Hut 8’s timing discrepancy is flagged beside the chart and preserved in exports. TeraWulf’s completed Abernathy divestment is reflected in its operating context. The existing PR and Drive preview are updated in place.

## Interface refinement — November 14, 2026

The workspace now exposes its three analysis views as persistent, labelled buttons. Each has a short description on desktop and a selected state available to assistive technology. Changing views preserves search and peer filters; returning from a company preserves the comparison context. Search remains visible on phones, with secondary filters and ordering behind a labelled disclosure that reports changed choices. The empty state offers a direct reset with keyboard focus restored to search.

Visual direction: warm paper, dark evergreen, restrained sage accents, a compact monogram, serif headings, and tabular financial numbers. Monetary columns align on the right on desktop; mobile retains labelled company cards. Exports sit beside the comparison, and view-specific introductions explain what the current table answers. Avoid risk colors, decorative gauges or implied safety rankings.

Company briefs promote scheduled principal repayments immediately after the reported borrowing balance, ahead of the instrument inventory, reconciliation detail and leases. Persistent section navigation follows the reading position, supports keyboard jumps, and respects reduced-motion preferences. Evidence remains expandable near the assertion. The finance dataset and calculations are unchanged.

Design priorities for a subsequent pass: review real user feedback before adding more panels; consider column selection and saved peer groups only if comparison workflows need them. Preserve a compact working surface instead of adding a marketing hero or a dashboard of aggregate financial totals across dissimilar businesses.
