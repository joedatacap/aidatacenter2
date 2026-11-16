# Execution brief origin

https://docs.google.com/document/d/1T8O_BndzDK0ouvwCDXCg3vBBT3EjC4Isgy8GE4FWXE8

# Neocloud Watch V2

Nine-company implementation brief and autonomous Codex handoff

Prepared November 15, 2026 • Owner: Joe Wu • Repository: joedatacap/aidatacenter2

## 1. Mission and delivery mandate

Build a polished, fast research workspace that connects earnings, financing, and AI infrastructure delivery. Within 60 seconds Joe should understand material changes across his peers; within three minutes he should be able to explain one company’s operating progress, funding position, and next catalyst.

This is an execution brief. Implement, research, validate, commit, and prepare a reviewable PR. Do not stop after proposing another plan, after a mockup, or after finishing only the three benchmark companies. Complete the nine-company release within the evidence boundaries below. Make routine engineering and presentation decisions independently and record them. No repeated consultation with the planning assistant is necessary.

Keep the existing financing work. Build the four connected views Overview, Earnings, Financing, and Buildout around one company identity and evidence model. Preserve the wider existing universe behind an All companies filter; the nine named companies are the default focus set. No composite investment recommendation or safety score.

## 2. Selected companies and honest size labels

Benchmark peers: CoreWeave (CRWV), Nebius (NBIS), and IREN (IREN). These are the three anchor comparisons requested by Joe, not a claim that all three satisfy a large-cap threshold.

Medium-sized research group: Applied Digital (APLD), Hut 8 (HUT), and TeraWulf (WULF). Prioritize construction economics and customer commitments for Applied Digital; project-versus-parent financing and cash access for Hut 8; and delivery milestones, financing, and HPC revenue progress for TeraWulf. These research priorities are not quality rankings.

Smaller research group: WhiteFiber (WYFI), SharonAI Holdings (SHAZ), and Axe Compute (AGPU). Prioritize segment economics and capacity ownership for WhiteFiber; disclosed GPU deployment, contract conditions, and funding for SharonAI; and recognized revenue, customer prepayments, vendor obligations, share structure, and delivery progress for Axe. Include AGPU in the first implementation slice so smaller-company disclosure gaps shape the design early.

Keep business model independent of size: GPU cloud/operator, infrastructure lessor/developer, mixed mining/AI business, or other verified category. Assign current categories from issuer disclosures rather than inheriting stale labels. Model parent/subsidiary relationships and overlapping economic exposure; do not sum subsidiary and parent metrics as independent industry totals.

### Market-cap snapshot for selection

Provider-reported USD market caps dated November 13, 2026: CRWV $29.55B; NBIS $33.96B; IREN $7.71B; APLD $4.83B; HUT $6.91B; WULF $6.33B; WYFI $427.06M; SHAZ $807.73M; AGPU $89.37M. These observations support cohort selection, not independently reconciled valuation claims. Sources are listed in section 12.

Use separate fields for focus_group (benchmark, medium selection, smaller selection) and market_cap_band. Bands: large >= $10B; mid >= $2B and < $10B; small >= $300M and < $2B; micro < $300M; unknown when unresolved. The smaller selection includes microcaps. IREN is mid-cap under this snapshot, while remaining a benchmark peer. Never force a 3/3/3 market-cap distribution or silently replace a chosen company because its stock price changes.

Refresh observations at execution time and retain their dates. Reconcile share classes and material issuance where possible. Existing Nebius ratio restrictions remain until evidence resolves them; a new vendor value alone does not clear the blocker. For AGPU, check reverse splits, prefunded warrants, convertibles, and other capital-structure changes before claiming a reconciled capitalization. Keep reported basic capitalization separate from any explicitly defined diluted scenario. Conflicting providers should produce a visible qualification or withheld ratio, not an invented average.

## 3. Starting point and branch integration

Repository: https://github.com/joedatacap/aidatacenter2

Existing feature PR: https://github.com/joedatacap/aidatacenter2/pull/8

At planning review, PR #8 was open, draft, and unmerged; its head was fe3c96392b838891f54abb2911de103a6ef3e8f9 on feat/neocloud-v2-workbench. CI run 43614313894 reported success. Prior handoff recorded 153 Python tests and 114 browser checks. These are prior results, not validation of this new release.

Read current AGENTS.md, README.md, docs/HANDOFF.md, docs/WEBSITE_V2_PLAN.md, docs/WEBSITE_V2_RESEARCH.md, relevant issues, and current PR state before editing. Verify the state has not changed since this brief.

If PR #8 is merged, branch from current main. If still open, create a separate continuation branch from its latest head and prepare a stacked PR against that branch, documenting the dependency. Do not overwrite another task’s branch or duplicate the unfinished V2 implementation. Resolve routine integration conflicts yourself while preserving unrelated work. Do not merge PR #8 merely to begin this task.

Relevant existing files: neocloud/data/debt_directory.json; neocloud/data/website_v2.json; neocloud/directory.py; neocloud/website_v2.py; scripts/build_v2_workspace.py; v2-preview/index.html; v2-preview/workspace.js; v2-preview/workspace.css; tests/test_website_v2.py; tests/browser-v2/workspace.spec.cjs.

Keep the static frontend and Python build/validation path unless a concrete requirement proves a change necessary. Do not introduce a framework rewrite, new production database, paid service, or public exposure of the research backend. Existing scenario/runtime modules are not proof the public website has real-world scenario coverage.

## 4. Product and interaction contract

Overview: compact masthead, three source-linked material changes, primary company comparison table, and a short upcoming-events panel. Default to the nine-company focus set. Keep the table visible on a typical laptop without scrolling through a large hero or long methodology block.

Default columns: Company; Latest quarter; Revenue growth; Guidance change; Cash and debt; Delivery update; Next event. Display dated market cap as secondary company information or an optional column. A period ending date must remain accessible even when quarter names differ across issuers.

Earnings: quarter selector/history, recognized revenue, like-for-like growth, operating margin, adjusted EBITDA with its stated definition, operating cash flow, cash capex, prior/current guidance, sourced consensus where available, and concise quarter commentary.

Financing: retain borrowing components, instrument inventory, typed rates, cash restrictions, debt/market-cap caveats, and repayment schedules. Nest the existing repayment comparison here rather than removing it. Keep contractual principal distinct from accounting carrying value and leases distinct from borrowings.

Buildout: compare operating IT load, construction/commissioning milestones, contracts, disclosed hardware, ownership, customer acceptance, and original versus revised delivery targets. Capacity statuses are not additive stages of one total; a project can have contracted and operating portions.

Company brief: shared Overview/Earnings/Financing/Buildout navigation and one evidence panel. Include what changed, why it matters, and what to watch next, each supported by facts. A row preview can show those three items before opening the full brief.

Preserve filters and selections across views and back navigation. Add shareable URLs containing view, companies, and filters. Allow optional columns and up to nine selected peers without a three-company cap. Saved peer sets may use local browser storage with an explicit local-only label; accounts and cross-device synchronization are outside this release.

Keep the warm-paper/evergreen design unless visual testing reveals a clear problem. Use restrained color, aligned tabular numerals, sticky company labels/headings, and short trend charts. On mobile, show readable company cards and accessible horizontally scrollable detail tables. Distinguish not disclosed, not researched, not applicable, stale, and conflicting evidence. Do not show zeros for missing values.

Use keyboard navigation, visible focus, meaningful selected states, reduced-motion support, and understandable empty/error states. Material caveats stay beside affected numbers; longer methodology can be expanded on demand.

## 5. Earnings and promised-versus-delivered logic

Evaluate separate signals: revenue versus pre-release expectations; guidance raised/maintained/cut; delivery versus a previously stated target; cash and financing changes; and stock-market reaction. Do not collapse these into a win/loss record or opaque overall verdict. A revenue beat can coexist with a guidance cut or delayed deployment.

For consensus, store the estimate, metric, accounting basis, currency, fiscal period, provider, and observation timestamp before the release. If the original pre-release estimate cannot be sourced, show unavailable and compare to prior management guidance separately. Never use a revised post-release estimate as the pre-release benchmark. Do not compare adjusted EPS to GAAP EPS.

Guidance changes compare the same metric, entity scope, and future period. Store old and new ranges; midpoint changes are explicitly derived. New guidance is not automatically a raise. If the period or basis changes materially, show not comparable. Percent changes with zero or negative comparison bases require an appropriate absolute change or N/M label.

Store original management targets as immutable dated observations, subsequent revisions, expected completion dates, and actual disclosed outcomes. Use met, missed, revised, pending, or insufficient evidence only where the record supports that classification. A missed deadline without a disclosed outcome is unconfirmed status, not automatic evidence of non-delivery. Link capacity acceptance and revenue recognition only when the source establishes the relationship.

Market reaction: define event time and trading-session treatment, then calculate pre-release close to the first full post-release session close and to the fifth session close where available. Adjust for splits, label price-return versus total-return basis, and keep broad-market comparison separate. Do not label a live daily change as an earnings reaction or imply that earnings alone caused a move.

## 6. Data model, sourcing, and import rules

Use stable company IDs with ticker aliases, exchange, issuer identifiers, business model, focus group, and dated size observations. Add structured records for quarterly results, guidance observations, consensus snapshots, capacity observations, milestone commitments/outcomes, market observations, material events, and evidence. Choose additive JSON/schema changes that fit the existing builder.

Every material numeric fact needs value or explicit missing status, units/currency, metric definition, entity/segment/project scope, period or effective date, publication date, retrieval time, source URL, supporting excerpt, and review status. Derived fields need input IDs and a named formula/version. Preserve both as-reported and restated observations when they differ. An extraction timestamp is not the financial statement date.

Quarterly results must distinguish three-month, year-to-date, annual, and trailing periods. Derive quarter cash flow from compatible YTD figures only when both inputs and the method are preserved. Restatements and fiscal-year changes must not silently alter comparisons. Cash capex and noncash equipment financing/lease additions are separate.

Primary sources: issuer earnings releases, investor presentations, SEC filings and exhibits, and official milestone announcements. Use secondary sources for discovery or attributed context; market data providers may supply dated market observations. No paywall circumvention or unapproved subscriptions. Do not hard-code data into UI rendering functions.

Existing Earnings Watch: https://datacap.xyz/cohorts/compute/earningswatch/

Source JSON: https://datacap.xyz/cohorts/compute/earningswatch/earnings.json

The inspected JSON says as_of August 31, 2026 and Q2 2026, with 18 reported records and 12 upcoming entries. Treat it as a historical import source, not current earnings coverage. Revalidate important records against linked primary sources. Do not carry forward categorical claims such as RPO equaling all legally enforceable obligations, or interpret a press release versus filing distinction as an investment conclusion without analysis.

Write a documented import adapter with stable IDs and deduplication by company, period, metric, scope, and revision. Do not import narrative verdicts as verified facts. Correct stale categories, including Nvidia being grouped with hyperscalers. Keep source-site code and deployment untouched in this task; establish the new repo’s reviewed dataset as authoritative for this release. A later cross-site migration can reuse its output.

Retain all existing companies and source records. Only the focus view defaults to nine. Refresh the latest available report for each focus company as of the execution cutoff; aim for four comparable quarters, accepting shorter histories or explicit missing fields where disclosure is insufficient. Include all nine in the coverage matrix rather than silently dropping difficult names.

## 7. Financial safeguards and scope limits

Never mix operating IT MW with utility MW, contracted capacity, commissioning capacity, GPU counts, ARR, or contract value. Keep physical site and company totals separate; prevent overlapping phases and joint-venture ownership from double counting.

Never infer company-wide cost of debt from selected coupons. Floating all-in rates require a dated benchmark; market yields, contractual rates, and accounting effective rates are distinct. Annual maturity buckets do not establish exact rolling 12/24/36-month repayments.

Restricted project cash is not unrestricted parent liquidity. Facility commitment is not drawn debt or freely usable cash. Project guarantees are not company-wide guarantees. Backlog, RPO, total contract value, prepayments, revenue, and ARR retain their issuer definitions. A large capex program is neither automatically good nor bad.

Keep mining/crypto, hosting, GPU-cloud, and other segments separate where disclosed. Do not infer GPU ownership from a tenant deployment or utilization from energized power. No unsupported per-GPU economics, funding runway, EV/MW ranking, or composite health score.

For AGPU use the same evidence rules as every peer. Use public sources for public output; private company information from Joe’s work context is not source material for this website. Flag share-count and business-transition comparability issues factually, without favorable or unfavorable editorial bias.

Defer authentication, paid/live data subscriptions, automatic publication of AI-extracted facts, buy/sell recommendations, elaborate scenario engines, and unrelated site/deployment changes. The site should work from its reviewed snapshot without a database, inference service, or quote API.

## 8. Implementation sequence and milestone acceptance

Milestone A: Baseline and schema. Inspect branches and tests; capture current behavior; record latest report and research status for all nine; add company aliases and typed historical records; implement the Earnings Watch adapter. Acceptance: repeat imports are idempotent, old data remains intact, unknowns retain their reasons, and dated market-cap bands are separate from selected cohorts.

Milestone B: First complete workflow. Implement Overview and Earnings plus connected Financing and Buildout briefs for CRWV, NBIS, IREN, and AGPU. Include one factual promised-versus-delivered timeline where sources permit, otherwise an explicit coverage gap. Acceptance: filter and deep-link behavior works, each takeaway opens its evidence, and at least one updated quarterly fact appears consistently in overview, brief, and export.

Milestone C: Full nine-company coverage. Add APLD, HUT, WULF, WYFI, and SHAZ; target four quarters for each and preserve the wider universe. Acceptance: all nine have a latest-report verification status, source-linked brief, financing coverage status, operating evidence status, and next-catalyst status. Sources unavailable after a bounded search produce an actionable gap record; incomplete disclosure never becomes a fabricated metric.

Milestone D: Finish and verify. Add exports, local saved peers if useful, correction history, documented refresh command, and staged update detection. Run the tests and visual checks below. Deliver a deployable static build, standalone offline preview, and reviewable PR with final screenshots, coverage matrix, and exact validation results.

Continue from one milestone to the next without routine approval requests. Milestones are execution checkpoints, not mandatory pauses. Prioritize correctness and a complete nine-company workflow over cosmetic extras. A working UI with unresearched data is not a fully researched release; report both completion states.

## 9. Update workflow and operational boundary

Implement a manual refresh command and a dry-run change-detection workflow. Where free approved sources permit, detect new issuer releases/filings and stage candidate evidence with old/new differences. New facts remain pending until reviewed through the documented repository process. Re-running the same source must not duplicate events or revise history invisibly.

Maintain separate freshness indicators for earnings, balance-sheet evidence, operating milestones, and market data. A fresh quote must not make an older earnings record look refreshed. Mark confirmed versus estimated future event dates; age expired upcoming events into a reconciliation queue rather than leaving them upcoming indefinitely.

Prefer cached daily market observations with explicit timestamps over an unlicensed live feed. Prove data-provider usage and redistribution terms before adding automated public distribution. If that cannot be established within available access, retain manually reviewed snapshots and document the gap.

Do not enable a recurring production workflow or claim continuous monitoring as part of creating this brief. Prepare the workflow and run its bounded manual checks. A running Codex task can execute this plan within its available tools and session limits; the document itself does not schedule or host an ongoing agent. Save durable progress so a resumed task can continue cleanly.

## 10. Tests and release acceptance

Financial tests: correct quarter/YTD alignment; fiscal/calendar differences; GAAP/adjusted separation; missing and negative denominators; source-linked calculations; cash/capex treatment; original and revised guidance; no future estimates used for historical surprises; market observation dates; split handling; unresolved capitalizations; capacity overlap; parent/project scope; idempotent imports; preservation of existing debt calculations and repayment reconciliation.

Browser tests: all nine focus companies and the broader universe are reachable; search, filters, sorting and saved views work; filters persist across navigation; shared URLs restore state; unknowns do not rank as zero; all four views and company sections work; exports match the screen and retain exact amounts, definitions, dates, sources and missing reasons; quote/feed failures do not block the snapshot.

Visual/accessibility checks: inspect 390px mobile and 1440px desktop at minimum, plus the existing 320/768/1100px responsive checks where supported. No page-level horizontal overflow, clipped labels, invisible keyboard focus, or overlapping sticky elements. Intentional table scrolling is permitted. Check the standalone offline preview with network access disabled.

Run the repository’s applicable full Python and browser suites and packaging dry runs before handoff. Report actual commands, pass/fail counts, and skips; do not reuse prior CI counts as current proof. Resolve failures caused by this work. If an environment prevents a check, state exactly what is unverified and continue independent checks.

Release gate: nine profiles; verified latest-report status or explicit source-access limitation for each; four usable views; source-backed key facts; no fake values; preserved existing financing behavior; working exports and offline preview; passing available tests; reviewable PR. Data completeness is reported separately from software readiness.

## 11. Autonomous working agreement and required handoff

Within this task, independently make reversible implementation choices, research public sources, fix regressions, create branches/commits and prepare PRs. Keep working through ordinary data gaps and test failures. Prefer the established stack and current design. Do not ask Joe to approve every company field, component, research attempt, or milestone.

Pause only for genuinely unavailable credentials/access that block all useful progress, new spending, destructive changes, or decisions outside the stated scope. Continue unblocked work and report a narrow question with a recommended default when a pause is necessary. Do not ask Joe to relay routine messages between agents.

This brief authorizes implementation and a reviewable handoff, not a new production merge or deployment. Check any exact existing release authorization independently; do not transfer permission from another repo or an older release. Complete the reviewable work before seeking any final publication decision.

At startup, copy this brief into docs/NEOCLOUD_WATCH_V2_EXECUTION.md and retain the Google Doc link as its origin. Maintain docs/NEOCLOUD_WATCH_STATUS.md with completed work, current branch/commit, evidence gaps, decisions, test results, and the next concrete action. Use docs/NEOCLOUD_WATCH_COVERAGE.md for the nine-company field/period matrix. These repo files become the execution record so another session can resume without reconstructing chat history.

Final handoff must include PR link and base/dependencies, commit SHA, working preview location and offline artifact, completed scope, exact tests, coverage gaps, market-data policy, refresh instructions, and remaining release steps. If Google Doc updates are available, append a concise status and PR link; otherwise updating the repo records is sufficient. Do not block delivery on access to Google Docs.

If the task reaches a session limit, commit a coherent checkpoint and leave a precise resume command/task in STATUS. Do not claim background work will continue when no task is running.

## 12. References and launch instruction

Prior product plan: https://docs.google.com/document/d/1ejfe4qo5nLJMwGOCclzTo9IqmRscHcrG0Spu6HkM-MU/edit

Research coverage: https://github.com/joedatacap/aidatacenter2/blob/feat/neocloud-v2-workbench/docs/WEBSITE_V2_RESEARCH.md

Prior verified CI: https://github.com/joedatacap/aidatacenter2/actions/runs/43614313894

Existing interactive preview: https://drive.google.com/file/d/1kko3A90R_Djzm49C1UmkKUiV77QGpG1b/view

Market-cap selection sources (all read for the November 13, 2026 observation; recheck before production use):

https://stockanalysis.com/stocks/crwv/market-cap/

https://stockanalysis.com/stocks/nbis/market-cap/

https://stockanalysis.com/stocks/iren/market-cap/

https://stockanalysis.com/stocks/apld/market-cap/

https://stockanalysis.com/stocks/hut/market-cap/

https://stockanalysis.com/stocks/wulf/market-cap/

https://stockanalysis.com/stocks/wyfi/market-cap/

https://stockanalysis.com/stocks/shaz/market-cap/

https://stockanalysis.com/stocks/agpu/market-cap/

These are provider observations and do not establish share-class reconciliation, investment merit, or equivalent business models. Operational classifications and current fundamentals must be refreshed from issuer evidence.

### Paste into the existing Codex project

Implement the Neocloud Watch V2 execution brief in joedatacap/aidatacenter2. Read this Google Doc in full: https://docs.google.com/document/d/1T8O_BndzDK0ouvwCDXCg3vBBT3EjC4Isgy8GE4FWXE8/edit . Inspect the current repo and PR #8, preserve its work, and execute all four milestones for the nine selected companies. Make routine decisions independently, record progress and decisions in the repo, and continue through implementation, research, tests, and a reviewable PR. Do not stop at another plan or after the first three companies. Do not merge, deploy, or buy services under this task. If you cannot access the Doc, request its exported text/Markdown once; after receiving it, proceed without routine consultations.

## 13. Multi-page design and second-repository integration

This refinement makes the four views in section 4 distinct, directly addressable pages sharing one application shell and one reviewed dataset. It supersedes any interpretation of that section as four modes of a single long screen. Preserve the financing workspace as a first-class destination, with its existing depth. Keep implementation in joedatacap/aidatacenter2; inspect the second repo as a read-only source/reference, not a repository to merge wholesale.

### Navigation and routes

Persistent top navigation: Overview | Financing & Debt | Earnings | Buildout. Shared controls: company search, focus group, business model, size band, selected peers, and source freshness. Use a compact top bar on desktop and accessible compact navigation on mobile. Preserve peer selection and filters across pages and back/forward navigation.

/overview/ (and site root): default nine-company comparison, three material changes, upcoming events, and links to the deeper pages. Purpose: determine which company deserves attention. Do not reproduce every detailed chart here.

/financing/: full financing comparison and company borrowing data. Secondary navigation: Debt & rates | Cash & funding | Repayments. Show carrying debt/principal distinction, rate scope, maturities, restrictions, recourse, collateral, and guarantees. Preserve the existing repayment schedule view; annual periods retain issuer calendars. Use coverage-qualified charts rather than unsupported sector-wide totals.

/earnings/: upcoming reports, reported results, and history. Secondary navigation: Upcoming | Results | History. Include release/filing/transcript links, separate revenue/guidance/delivery signals, concise call insights, and defined market-reaction windows. Company summaries should link directly to relevant financing and buildout evidence.

/buildout/: operating capacity comparison, project/phase timeline, and promised-versus-delivered history. Secondary navigation: Capacity | Projects & milestones | Customers & contracts. Show ownership, status, IT/power units, dates, customer acceptance, and whether revenue has begun when disclosed. Use projects/contracts as research objects linked to companies; no separate large map project is required for this release.

/companies/{company-id}/: shared company profile reached from any page, with Summary | Financing | Earnings | Buildout sections. Use stable IDs and ticker aliases. Support deep links to a section and selected fiscal period. Opening a profile must preserve a clear return path to the originating comparison.

These are routes within one website, not four separately maintained apps. Generate static route directories or use a verified host rewrite strategy; deep-link refresh must work on the actual static hosting target. The offline HTML may use equivalent hash routes while preserving the same page/navigation behavior. Keep base paths configurable rather than assuming domain root.

### Page composition and interaction examples

Financing page: short scope/freshness line, shared peer filters, debt/cash/rate comparison table, then selected-company repayment chart and instrument drill-down. Source drawers expose definitions and excerpts without forcing the reader away from the comparison.

Earnings page: compact upcoming strip, results table with fiscal-period end dates, then expandable report cards. A card separates reported metrics, guidance change, management-call insights, and market reaction. Link a raised capex guide to Financing > Cash & funding and Buildout > Projects & milestones for the same company and period.

Buildout page: operating capacity and status table first, milestone timeline second, customer/contract drill-down third. Clicking a delayed milestone opens its original dated target, later revision, and funding/customer context if evidenced.

Overview connects the three research pages: earnings describes performance, buildout describes delivery, and financing describes obligations and funding. Example navigation: select NBIS and CRWV on Overview; open Earnings to compare guidance; move to Financing with the same peers; open a company’s Buildout section to inspect deployment targets. Back navigation restores the prior comparison state.

Market prices and capitalization are a secondary strip or optional columns across pages. Do not add a fifth top-level Market page in this release. Keep sources/methodology accessible through a common panel/footer. Do not add sentiment feeds or sector rankings to the primary navigation.

### Verified reference repo and reusable pieces

Repository: https://github.com/joelingo2060/athenagent2team

Read-only inspected snapshot: 51b2ca7cc767fddef3ff732dd9929528631aab63 (main at inspection; refresh when execution begins).

Earnings Board rendered page: password/neocloud/index.html

Structured source: password/neocloud/data.json

Declared data contract: password/neocloud/schema.json

Deterministic renderer: scripts/build_neocloud.py

The inspected JSON contains 24 reported entries, two upcoming entries, 16 company profiles, and 30 deal records. All nine focus tickers appear in reported results. The latest entries include NBIS November 12, CRWV November 10, WULF November 6, IREN November 5, HUT November 4, and APLD October 7. WYFI, SHAZ, and AGPU latest entries in this file remain in August. These are repository record dates, not independent verification that each issuer’s latest report is covered.

Reusable UX concepts: upcoming report cards with what-to-watch; season timeline; reported-quarter metric cards; management-call takeaway and more-than-the-release callouts; categorized filing/IR/transcript links; dated analyst actions; reported-event histories; what-changed strip; defined post-report returns.

Adapt these into the new Earnings page and company sections rather than transplanting the entire long generated page. Keep the established financing site typography and navigation consistent. Source data and renderer are reusable references; narrative conclusions still require evidence review. Broad company profiles/deals can seed research candidates for Buildout and Financing but are not automatically verified facts.

### Import issues to resolve before reuse

The inspected file has updated='2026-11-16 12:41' without an explicit timezone, as_of='2026-08-21', and stale=false. Do not treat these as a reliable single freshness timestamp. The renderer passes as_of to reported-card rendering, so stale global dates can affect age/context displays. Preserve raw metadata and derive reviewed per-record dates with explicit timezones where known; do not invent a timezone.

The schema and current records diverge: fields such as rev_vs versus rev_vs_consensus and net_loss versus loss require explicit alias mapping; some newer records omit company while the declared schema requires it. Resolve company names from a canonical registry, preserve the imported source record, and validate normalized output. Missing fiscal periods must be established from issuer evidence, not inferred solely from release dates.

Many financial fields are free-text strings. Parse only unambiguous amounts, units, currency, period, and scope; otherwise retain display text as an unverified research candidate. Add numeric fields only when evidence supports them. Do not permit free-text parsing to manufacture comparable financial ratios.

The schema describes a publisher named neocloud_site_publish.py and an external monitor/staging flow; that publisher was not present in the inspected repository tree. Its recurring operation, validation, SEC auto-resolution, and return-calculation correctness are not verified by this review. Reuse only inspected code, independently test calculations, and do not claim an inherited working automation.

Treat drift_3d as a separate T+3 source field, not as T+1 or T+5. Recompute the new release’s requested return windows from dated price observations or retain an explicitly labeled unavailable state. Do not silently change the horizon. Preserve source/date attribution for analyst actions; historical summaries are not current consensus.

Do not import the aggregate beat/miss win-loss scoreboard or sector bull/bear meter as the new site’s quality ranking. The new earnings assessment retains separate performance, guidance, delivery, funding, and market-reaction dimensions.

This is a private multipurpose repository. Limit import to the relevant neocloud files and public-source-backed facts; exclude unrelated team dashboards, credentials/configuration, operational logs, and internal strategy sections such as aethir_bridge from public output. This task does not authorize publishing the private repo or its internal material wholesale.

### Acceptance additions for the multi-page release

Each top-level page has a stable URL, active navigation state, useful direct-entry layout, and preserved peer filters. Reloading any page or company detail works in hosted preview; browser back/forward restores state; offline preview navigation also works. Financing remains independently useful and includes existing rates, cash restrictions, and repayment functionality.

Add integration fixtures from the second repo that exercise alias normalization, missing company fields, stale global dates, missing fiscal periods, and T+3 versus T+1/T+5 distinctions. Imported records must pass the same source and financial validation as native data. Keep the import read-only with respect to athenagent2team; document the exact source commit and imported paths.

Extend the existing four milestones rather than creating another competing project plan. The next Codex task should read this section alongside the rest of the brief, inspect the relevant second-repo files if accessible, and deliver the same nine-company release as a connected multi-page site. If the second private repo is inaccessible in that environment, proceed using the public Earnings Watch adapter and primary issuer sources, logging that the richer reference import remains unavailable. Do not block all implementation or repeatedly ask Joe to relay files.
