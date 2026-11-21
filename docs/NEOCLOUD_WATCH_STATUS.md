# Neocloud Watch V2 — execution receipt and resume guide

See the [current release receipt and publish procedure](NEOCLOUD_WATCH_RELEASE.md) for the public version and canonical main revision.

## Homepage and public source as of November 20, 2026

The public Neocloud Watch project is `appgprj_6afb8d8562c0819183402d9c41093312`. Its homepage is [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/). The application source is on `joedatacap/aidatacenter2`, branch `feat/neocloud-watch-v2`. The Sites repository tracks the corresponding generated static files on `main`. Its `maintenance/GITHUB_SOURCE.md` identifies the exact application commit used for publication.

Overview shows the latest reported releases, up to four quarters of revenue, statement-date cash and financing obligations, selected project milestones and the shared filterable table. The same peer selection drives the charts, rows, exports and links to the other three pages. The financial cutoff is November 17. Nine companies have 34 reviewed quarterly observations between them. Ten contextual companies have limited coverage.

Read the [source reconciliation](NEOCLOUD_WATCH_SOURCE_RECONCILIATION.md), [original audit](NEOCLOUD_WATCH_AUDIT.md) and [current coverage](NEOCLOUD_WATCH_COVERAGE.md) before refreshing a record. Rebuild with `npm run build:watch`, run `npm run test:watch`, and compare the complete generated site with the current Sites source tree before publishing. The dated receipts below describe earlier versions.

## November 16 delivery

Updated November 16, 2026. Reviewed cutoff: **2026-11-16T05:36:00Z** (00:36 America/New_York). Individual statements, releases, operations and equity observations retain their own dates.

Origin: [execution brief, including Section 13](https://docs.google.com/document/d/1T8O_BndzDK0ouvwCDXCg3vBBT3EjC4Isgy8GE4FWXE8/edit), copied in full to [NEOCLOUD_WATCH_V2_EXECUTION.md](NEOCLOUD_WATCH_V2_EXECUTION.md). Older financing plans are background context.

## Integration and boundaries

- Branch: `feat/neocloud-watch-v2`, from verified PR #8 head `fe3c96392b838891f54abb2911de103a6ef3e8f9`.
- PR #8 remains open/draft/unmerged. This release is a **stacked PR against `feat/neocloud-v2-workbench`**, dependent on #8. Do not merge #8 simply to begin or automatically retarget without checking its eventual merge method.
- Original directory, financial calculations, runtime agents, database schemas, V1 preview and earlier V2 preview remain preserved. New application and reviewed data are additive.
- No merge, deployment, purchase, recurring production monitor, database change, inference call or live quote feed was performed.

## Milestones completed

**A — baseline and schema:** inspected branches, AGENTS, current PR and prior evidence. Canonical registry retains the original16 plus WYFI/SHAZ/AGPU. Cohorts are independent of dated market-cap bands. Typed quarterly observations, source metadata, guidance originals/revisions, delivery milestones and explicit missing states validate before build. Read-only earnings adapter has stable logical IDs, alias mapping, per-record period review, source provenance and no automatic fact promotion.

**B — connected workflow:** four directly addressable pages plus company profiles; root defaults to Overview. Shared filters, up to nine selected peers, optional market-cap columns, local-only saved peers, company sections, fiscal periods and exact originating secondary view survive URL navigation/back/forward. Existing debt instruments, cash restrictions, typed rates, principal/carrying bridges, leases and issuer-calendar repayment schedules remain accessible.

**C — all nine researched:** six benchmark/medium names have four consecutive quarters each; WhiteFiber has four; SharonAI and Axe have two each with bounded-source research gaps. Total32 quarterly history observations. All nine have latest-report verification, financing/operating coverage and next-catalyst status. Source-backed CoreWeave original/current guidance pairs, IREN original/revised ARR target, and WhiteFiber original target/outcome are represented without a composite score. The wider19-company universe is reachable.

**D — tested static release:**24 actual static routes, configurable base path, offline hash-route artifact, CSV and evidence JSON, source drawers, local saved peers, correction history, refresh/staging commands, coverage matrix and screenshots. Software workflow is complete; research coverage remains partial as detailed below.

## Research completeness and evidence limits

Read [coverage matrix](NEOCLOUD_WATCH_COVERAGE.md), [six-company evidence review](NEOCLOUD_WATCH_RESEARCH_MAIN.md), and [smaller-company review](NEOCLOUD_WATCH_RESEARCH_SMALL.md).

- Reviewed snapshot contains219 linked evidence records, including inherited financing evidence,45 new issuer sources and nine refreshed provider observations.
- SHAZ Q3 is scheduled after close November16; AGPU's corrected call is November17,08:30ET. Q3 results were not yet available at cutoff. Their latest reviewed financials remain June30. A corrected future date never becomes a fabricated result.
- Quarter-specific cash-flow/capex history remains incomplete. HUT Q3 and WULF Q4 derived fields retain compatible cumulative inputs and formula IDs. IREN's later comparative source publication is distinguished from the unavailable original release date.
- Original pre-release consensus snapshots and dated split-adjusted T+1/T+5 return windows remain unavailable. Imported T+3 stays separate. No invented beat/miss results or live daily change relabelled as earnings reaction.
- CoreWeave FY2026 guidance compares the source-backed August11 and November10 ranges. Historical report views exclude later revisions; guidance remains separate from consensus.
- Provider market caps remain dated November13 even after execution-time review. Existing financing ratios retain their actual historical equity denominators and dates; new smaller-company ratios keep explicit share-structure blockers. Nebius, SharonAI and Axe capitalization reconciliation remains incomplete. No automated public market-data redistribution license is claimed; only attributed manual snapshots are used.
- Parent/project cash access, lease/debt distinctions, tenant versus owned GPUs, overlapping capacity phases, minority ownership, group versus segment revenue, and Hut8's inherited repayment timing discrepancy remain visible. WYFI's Bit Digital parent relationship and AGPU's business transition, warrants/splits and later obligations are qualified. No sector financial totals or safety ranking are inferred.

## Read-only reference provenance

`joelingo2060/athenagent2team` main was freshly verified at `51b2ca7cc767fddef3ff732dd9929528631aab63`. Only four task-relevant paths were inspected: `password/neocloud/index.html`, `data.json`, `schema.json`, and `scripts/build_neocloud.py`. That repo was not modified. The raw multipurpose payload stays ignored under `work/`; private strategy, credentials, unrelated dashboards, aggregate verdicts and sentiment were excluded. Metadata-only audit is `neocloud/data/watch_import_audit.json`.

Adapter aliases include `rev_vs`→`rev_vs_consensus` and `net_loss`→`loss`; missing company names use the canonical registry. The reference's timezone-free `updated` and stale global `as_of` are not financial freshness. Free-text candidates are not parsed into comparable financial values. All14 focus candidates require review; no candidate was automatically promoted. Primary issuer evidence supplies the release's public numeric facts.

Public Earnings Watch JSON was attempted through HTTPS (proxy CONNECT403) and the web connector (inaccessible). No repeated retries; fixtures cover its adapter shape and the richer accessible reference supplied research candidates.

## Validation receipt

- `python3 work/run_watch_python.py`: **175 passed**, no skips, including three real disposable TLS Postgres integration checks. This ignored local harness injects only the isolated test database URL. Reproduce with a dedicated `TEST_DATABASE_URL` and `python -m pytest -q`. Never use production for these tests. One existing FastAPI/Starlette deprecation warning remains.
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run test:preview`: **76 passed**.
- Same environment, `npm run test:v2`: **38 passed**.
- Same environment, `npm run test:watch`: **34 passed**. Includes four pages, all19 profiles, nine peers, URL/back/forward state, nested base paths, financial formatting, historical guidance, source escaping/unsafe links, error recovery, exports and exact offline bytes with networking disabled.
- `npm run deploy:dry-run`, `npm run deploy:subpath:dry-run`, `npm run deploy:watch:dry-run`: passed; no deployment.
- `python -m compileall -q neocloud`, `node --check watch-preview/watch.js`, `git diff --check`: passed.
- Offline Chromium screenshots and20 page/viewport combinations checked at320/390/768/1100/1440px; no page overflow or script errors. Intentional detail-table scrolling remains available.
- Manual candidate import:14 staged differences, repeat import0 differences. Live public SEC filing fingerprint:1 pending review candidate; no extraction or publication.
- Final CI result and PR/preview links are recorded in the delivery receipt below. Earlier PR #8 results are not reused as proof of this release.

## Build and preview

```sh
python3 -m pip install -e '.[test]'
npm ci
npm run preview:watch
# http://127.0.0.1:8003/overview/
```

`npm run build:watch` generates `work/neocloud-watch-site/` (serve this directory) and `work/Neocloud-Watch-V2.html` (download and open; Drive viewer does not execute HTML). Profiles are `/companies/{stable-id}/`; primary pages are `/overview/`, `/financing/`, `/earnings/`, `/buildout/`. Every hosted route has an actual index.html, so refresh needs no SPA fallback. Base path: `python3 scripts/build_neocloud_watch.py --base-path /research/ --output work/custom-site`; mount that output at `/research/`.

`npm run deploy:watch:dry-run` uses `wrangler.watch.jsonc` with static assets only, no routes or backend bindings. This is a review configuration, not permission or configuration to deploy to any production hostname. Production credential/domain review remains a separate release task.

## Manual refresh and review

```sh
# Normalize only whitelisted earnings candidates; never publishes them.
python3 scripts/import_earnings_watch.py /path/to/reference.json --output work/watch-candidates.json
# Stage source changes, retaining old/new values and explicit pending review.
python3 scripts/refresh_neocloud_watch.py --input /path/to/reference.json --baseline work/previous-review.json --output work/next-review.json --dry-run
# A bounded issuer HTML/filing fingerprint detects changes without extracting facts.
python3 scripts/refresh_neocloud_watch.py --evidence-url https://issuer.example/public-release --baseline work/previous-issuer-review.json --output work/issuer-review.json --dry-run
```

Review a candidate against public primary evidence; retain excerpt, units, accounting definition, scope, period, source publication/retrieval and original/revised history. Add reviewed facts to `watch_benchmarks.json` or `watch_smaller.json`; dated market observations belong in `watch_markets.json`. Rebuild, run financial/browser checks, and regenerate `python3 scripts/build_watch_coverage.py`. Never replace dates merely to make freshness appear current. Expired upcoming events belong in reconciliation, not an automatically rolled-forward calendar. No scheduled production workflow is enabled.

## Resume and remaining release steps

Start by inspecting git status, this receipt, the coverage matrix and both PRs. This implementation is complete as a reviewed static release; further financial enrichment should be a new focused research change. First research follow-up: retrieve SHAZ/AGPU Q3 after their confirmed events, reconcile share structures, and complete missing quarterly cash-flow/capex and market-reaction inputs. Preserve earlier observations.

For eventual public release: review dependency PR #8 and this stacked PR; choose the integration/retarget method; confirm deployment authorization, Cloudflare access and hostname; deploy a preview; verify actual hosted behavior and freshness; only then consider production. Nothing in this task authorizes those merges or deployments. No coding or monitoring continues after the task ends.

## Delivery links and verified implementation

- Reviewable [PR #9](https://github.com/joedatacap/aidatacenter2/pull/9), base `feat/neocloud-v2-workbench`, dependent on [PR #8](https://github.com/joedatacap/aidatacenter2/pull/8).
- Implementation commit: `d2b8eaf804b8d38619d96786942207d31a7f0273`. Final delivery bookkeeping follows as a separate documentation-only commit; `git rev-parse HEAD` identifies that branch head.
- Implementation [CI run43811849478](https://github.com/joedatacap/aidatacenter2/actions/runs/43811849478) **passed**:175 Python tests,76 preview browser checks,38 earlier V2 browser checks,34 Watch checks and all three packaging dry runs. The current PR also exposes checks for the final documentation-only head.
- [Working interactive preview](https://drive.google.com/file/d/1qPnbuu9L6b9NDFaprh1nQZEe45oUImmc/view): download and open in a browser. No network is required after download.
- [Review folder: six screenshots and static-site ZIP](https://drive.google.com/drive/folders/1XjY3VYjBl4ogf0QGvtyW-IE4-PKjlyuh).
- [Deployable static-site ZIP](https://drive.google.com/file/d/1dEYTtKudtjSMhWdA5JrQ79vCFwJgMQFl/view). Contains only28 generated website files:24 route indexes, JavaScript, CSS, reviewed JSON and security headers. No backend, credentials or private reference payload.
- Preview screenshots: Overview, Earnings, Financing and Buildout at1440px; Overview and Axe financing at390px. Additional320/768/1100px layout checks passed.
- Google execution brief updated with implementation receipt, limitations and PR link. The old V2 preview and Drive files were preserved.

Disposable local TLS Postgres was stopped after the tests and its temporary credential removed. No application/Neon database was touched. There is no unattended research or publication job running.

## November 17 follow-up — concise earnings-call reads

Added **Analyst read** above each quarter's metrics on Earnings and company profiles. All nine latest quarters already covered by the snapshot now have actual transcript-based reads (16 bullets);23 historical quarters have labelled release/filing interpretations. Each section has1–3 sourced bullets. The actual call date, evidence basis and analysis review date remain visible. Transcript review does not refresh the financial snapshot or imply new SHAZ/AGPU Q3 coverage.

See [call coverage and maintenance](EARNINGS_ANALYST_READ.md). Nine transcript sources were added without changing financial values. Existing exports retain the analysis within quarter records. The new validation prevents filing-only sources from being labelled as reviewed calls. Tests cover bullet limits, source identity, date separation, all-nine coverage, evidence drawers and historical fallback. This continuation remains on PR #9 and does not authorize a merge or deployment.

Follow-up verification:24 targeted Python tests and36 Watch desktop/mobile browser checks passed. A structural comparison against the prior commit confirmed that all existing financial values and source records remain identical after excluding the newly added analysis and transcript evidence. Full CI runs on the updated PR head; the prior implementation test receipt remains historical evidence.
