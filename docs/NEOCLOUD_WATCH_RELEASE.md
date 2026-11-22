# Neocloud Watch release and publication

The public site is [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/). GitHub `joedatacap/aidatacenter2` on `main` is the application source. ChatGPT Sites stores the generated static publication in its own source repository on `main`. A GitHub merge runs tests and packaging dry runs. Publication is a separate operation.

## November 22, 2026 stock-performance update

**Public release remains version 5.** The stock-first homepage and fifth page, Markets, are available in the GitHub build. Publication is held pending a price source with verified rights covering public display, cached history and exports. Building a local preview or merging source does not publish to Sites.

| Observation | Status |
| --- | --- |
| Public project | `appgprj_6afb8d8562c0819183402d9c41093312`, existing public audience. Version 5 deployment and source commit are recorded below. |
| Latest completed US session at the source check | November 20, 2026 at 21:00 UTC. Zero verified price histories acquired for the nine focus companies. The quote timestamp is unavailable. |
| Equity-size context | November 13 dated provider records. Six focus companies have a usable dated size band. Nebius, SharonAI and Axe Compute retain capitalization blockers. |
| Financial evidence | November 17, 2026 at 18:35:45.406835 UTC. The emitted financial file must match version 5 SHA-256 `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838` for this presentation-only release. |
| Next release gate | Obtain an entitled export, import it with the [refresh procedure](WATCH_MARKET_DATA.md), verify sample returns from the source closes and run the guarded build. Then follow the existing-site steps below. The [source audit](WATCH_MARKET_SOURCES.md) records which providers were checked. |

**Candidate source and QA.** Rebuild from [e461e0f83927a7639f78775286e436ae76bec356](https://github.com/joedatacap/aidatacenter2/commit/e461e0f83927a7639f78775286e436ae76bec356). Later receipt-only commits do not change its generated site. [PR #13](https://github.com/joedatacap/aidatacenter2/pull/13) records the merge to main. The candidate passed 216 Python checks including disposable TLS Postgres and 96 Watch browser checks across desktop and mobile. The [candidate CI run](https://github.com/joedatacap/aidatacenter2/actions/runs/44967910265) includes legacy and workbench regression tests and packaging. No Sites version was saved for this update.

**Release evidence.** The [November 22 production check](https://github.com/joedatacap/aidatacenter2/actions/runs/44967212699) exercised the existing version 5 over HTTPS. All 16 public desktop/mobile checks passed, including the served bundle and financial-file comparison, peer selection, sources, exports and original/revised Buildout dates. Local development could not reach the public origin through its proxy; the production results come from GitHub-hosted Chromium.

The candidate was checked at desktop and mobile widths. The checked-in market snapshot shows the source gap, and the guarded release build rejects it. Functional chart tests use isolated browser responses. Download the [offline candidate](https://drive.google.com/file/d/1htIEp8kkEFjnueyfFtlk1EfFlsKz3tqq/view) to try it locally. The [dated size table](https://drive.google.com/file/d/1JVOsoooZjtGq1-ZBLqhtmCRhlphr9bit/view) shows all nine focus peers. Candidate homepage screenshots show the actual price-availability state on [desktop](https://drive.google.com/file/d/1HUs64nfz1thgftskdZoSsyV8gTrFZf50/view) and [mobile](https://drive.google.com/file/d/1oUe2moXYvau5XYpsmu-1eERcNkb_hnZX/view).

## November 21, 2026 release receipt

| State | Source and evidence |
| --- | --- |
| Public site | Version **5**, public audience, [production homepage](https://neocloud-watch.gpuchips.chatgpt.site/). Sites confirmed deployment `appgdep_6b01b75857948191ae1afe54423c2867` succeeded at 15:23 UTC on November 21, 2026. |
| Previous deployment (version 4) | Deployment `appgdep_6b002589fa488191a3aee79a8f6734b4`. GitHub [5bf5d1ad8b8f6c2c1f255f247f4f0880723de902](https://github.com/joedatacap/aidatacenter2/commit/5bf5d1ad8b8f6c2c1f255f247f4f0880723de902), now in main history. Sites commit `2a21859e671f49de6a1951e1c252a3899efa56b2`. A clean rebuild matched all 29 files in that publication. |
| Canonical release on GitHub main | [PR #8](https://github.com/joedatacap/aidatacenter2/pull/8) merged at `128c07d63f2fce67ce654815a17fb4f8fea6ad9d`. PR #9 was retargeted to main. Both review findings were fixed and resolved. [PR #9](https://github.com/joedatacap/aidatacenter2/pull/9) merged at [ff7417ca8851c6488e40514d0a62460c2ae734d8](https://github.com/joedatacap/aidatacenter2/commit/ff7417ca8851c6488e40514d0a62460c2ae734d8). Its Git tree equals the tested PR head `727db69db02b85ec00b8e95397a7fd521c6746fd`. |
| Published release | Version **5**, Sites commit `2dc216a95a6e4264cc0ae14deb26a287f5edaee6`. Version ID `appgprj_6afb8d8562c0819183402d9c41093312~appgver_65279b0cf1d88191ae8128f565a01e25`. Before deployment, a clean output directory built from GitHub main `4f45fecbf0248cfbb29356ad98474bbe040890e4` matched all 29 files at this Sites commit byte for byte. The only GitHub change since the release merge was the runbook. |
| Data | Cutoff `2026-11-17T18:35:45.406835Z`. In both versions and canonical main, the exact file SHA-256 of `dist/data.json` is `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838`. The Axe and SharonAI Q3 corrections, fiscal dates, historical scopes and recorded market dates are preserved. |
| Version 4 to 5 | The only changed static asset was `watch.js`. Version 5 shows the recorded original and revised milestone windows on the Buildout page and company profiles. All homepage rendering code, route HTML, styles and financial inputs are identical. The other code fix creates the offline output directory on a first custom build. |
| Local build and CI | 179 Python tests, including disposable TLS Postgres, and 74 Watch desktop/mobile browser checks passed locally. [Final PR CI](https://github.com/joedatacap/aidatacenter2/actions/runs/44859523211) also passed 76 legacy and 38 workbench browser checks and all three packaging dry runs. These browser checks exercise built files on a local server and offline. |

**Version 5 production verification.** All 16 public checks passed in desktop Chromium and an emulated mobile Chromium viewport with touch. Both fetched `watch.js` and `data.json` from the public origin and compared their bytes to the main build. The renderer SHA-256 was `9df69412b05280272923046f62cf34d2a7f37b95cbefcf3a09ce68fffa790ace`; the financial file matched the November 17 checksum above. Peer selection, source drawers and CSV/JSON exports also passed. [GitHub Actions run 44919088688](https://github.com/joedatacap/aidatacenter2/actions/runs/44919088688)

The tests read each of these records on the live Buildout Projects page and the corresponding company profile:

| Company and milestone | Original target | Reviewed revision |
| --- | --- | --- |
| IREN, $4B ARR target | By December 31, 2026 | January 2027, potentially extending through February 2027 |
| Hut 8, initial River Bend data hall | Q2 2027 | No reviewed revision |
| Nebius, ARR target | December 2026 | February 2027 |

All three disclosed outcomes displayed “Not established.” These dates describe management targets.

**Historical version 4 production checks.** [Public smoke run 44860376208](https://github.com/joedatacap/aidatacenter2/actions/runs/44860376208) passed ten production checks using desktop Chromium and an emulated mobile Chromium viewport with touch. Both browsers reached the public URL, used the peer checkbox and search, followed a company link and opened source drawers to inspect their links, checked AGPU's buildout stage, exercised chart details, and downloaded and inspected CSV and JSON. The public renderer bytes matched v4 SHA-256 `4a71781cf49a93d45a84e17fe49fe201a4e8edd599cd382dd8bc07497f985279`. Public and main data had the same key-sorted JSON digest `13e3182bc5e5c67dd09765c7bbcd251cbf02670c9c4a3be7df2b54a7f70804bf`. Separately, the linked Axe and SharonAI Q3 SEC filings each returned HTTP 200 with HTML. The workspace proxy itself denied the public site with HTTP CONNECT 403. Production browser results come from GitHub-hosted runners.

The owner explicitly authorized publication of the existing saved version 5. Sites returned `succeeded` and the public HTTPS URL. A separate status read linked that deployment to the saved version, and the site access setting remained `public`.

## Update and publish

1. Read this release receipt, then fetch GitHub `origin/main`. Inspect open PRs and create a working branch from the current main. On Sites call `get_site` and `list_site_versions` for project `appgprj_6afb8d8562c0819183402d9c41093312`. Confirm the public URL and audience. Use `get_deployment_status` to identify the successful public version. Record its version, deployment ID and source SHA before making edits.
2. Open the **existing** Sites source repository using `create_source_repository_write_credential` for that project and the Sites source helper. Use the returned branch and short-lived credentials in memory. Read `.openai/hosting.json` and `maintenance/GITHUB_SOURCE.md`. Compare the remote HEAD and the current public commit, then compare published `dist/` with a fresh build of the GitHub commit it records. Reconcile any intervening edits before writing. The v3 `maintenance/source-corrections.patch` is historical and is already incorporated.
3. Edit canonical GitHub source. Homepage and views live in `watch-preview/`; inputs and validator live in `neocloud/data/` and `neocloud/watch.py`. For a financial update, review the dated primary evidence, scopes and reporting periods before editing observations. Refresh the coverage matrix with `python scripts/build_watch_coverage.py` if the research changed. See [data audit](NEOCLOUD_WATCH_AUDIT.md) and [source reconciliation](NEOCLOUD_WATCH_SOURCE_RECONCILIATION.md).
4. Install dependencies and run the release checks from the GitHub checkout:

   ```sh
   python -m pip install -e '.[test]'
   npm ci
   npx playwright install --with-deps chromium
   python -m pytest -q
   npm run test:watch
   npm run deploy:watch:dry-run
   ```

   Use a disposable TLS PostgreSQL database for the database integration tests. The GitHub Tests workflow provisions one and runs the existing preview and workbench suites too. Review CI and review threads before merging. Test the company links, sources, both exports, peer selection, charts and quarter dates. The hosted and offline suites run on desktop and mobile against a local build.
5. Fetch the accepted source commit, record its full SHA, and build from that exact revision into a new, empty directory. Use the root base for this public URL:

   ```sh
   stage_dir=$(mktemp -d)
   python scripts/build_neocloud_watch.py --release --base-path / --output "$stage_dir/dist"
   ```

   Inspect the staged file list and differences, including `data.json`, `audit.html`, `_headers`, assets and all route indexes. Version 5 has 29 files in `dist/`, including 24 route indexes. The Markets build adds `markets/index.html` and `market-data.json`. A failed release build stops publication, including reuse of any older staging directory. For a presentation or packaging change, compare `data.json` byte for byte with the previous publication. When generated files already match, retain the existing deployment.
6. For an authorized publication, update only the existing Sites checkout's `dist/` to match the staged tree. Record the full GitHub SHA in `maintenance/GITHUB_SOURCE.md`. Preserve the hosting manifest and all maintenance history. Verify with `diff -qr "$stage_dir/dist" "$site_checkout/dist"`, setting `site_checkout` to the path opened in step 2. Recheck the remote head and current version before pushing to prevent overwriting another publisher.
7. Follow the Sites source helper to commit, push and package. For a static Git checkout the equivalent archive command is `git archive --format=tar --output=/absolute/path/to/release.tar HEAD .openai/hosting.json dist` from the verified Sites checkout. The archive contains the manifest and generated output. Call `save_site_version` with the same project ID, **pushed Sites commit SHA** and unchanged archive, then `deploy_site_version` with the returned saved-version ID. Keep the existing public audience. If the call is pending, poll `get_deployment_status` until terminal. Verify `get_site` still returns the expected URL, version and access.
8. Run browser smoke checks on the actual public origin from a network that can reach it. On desktop and mobile, check a plotted quarter against the reviewed data, select a peer, open its company profile and a source, and inspect downloaded CSV and JSON. Compare public `/data.json`, `/market-data.json` and `/watch.js` with the staged files. For a Markets release also verify the default ranking, a second window, the scatter, the common history and that exports match the selected peers and dates. Record the origin, result and any access error separately from local tests. Update the release receipt with the GitHub SHA, Sites SHA, version, deployment ID, data cutoff, CI and browser results.

### Reproduce the version 5 production browser check

The [release QA revision](https://github.com/joedatacap/aidatacenter2/commit/cc5c10ad408dccefd88841e3e2e561d61794ee2f) contains the public Playwright checks for version 5. The checks compare the deployed JavaScript and reviewed data to the build produced in that checkout. Use a separate checkout. Install the Python test dependencies as in step 4, then run:

```sh
git fetch origin qa/neocloud-watch-live
git worktree add --detach ../watch-public-qa cc5c10ad408dccefd88841e3e2e561d61794ee2f
cd ../watch-public-qa
python -m pip install -e '.[test]'
npm ci
npx playwright install --with-deps chromium
npm run build:watch
env -u WATCH_SMOKE_LOCAL_CONTROL npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

With that variable unset, the test navigations and downloads use the public Sites origin. The test runner also starts a local server for its build control. A run with `WATCH_SMOKE_LOCAL_CONTROL=1` checks local behavior only. When publishing a newer version, use a QA worktree based on its accepted GitHub release commit, carry over the smoke spec, and compare the public assets with the generated release files. Keep the public target and checks of real interactions intact.
