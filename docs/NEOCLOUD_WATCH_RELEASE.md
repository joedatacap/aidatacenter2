# Neocloud Watch release and publication

The public site is [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/). GitHub `joedatacap/aidatacenter2` on `main` is the application source. ChatGPT Sites stores the generated static publication in its own source repository on `main`. A GitHub merge runs tests and packaging dry runs. Publication is a separate operation.

## November 21, 2026 release receipt

| State | Source and evidence |
| --- | --- |
| Public site | Version **4**, public audience, [production homepage](https://neocloud-watch.gpuchips.chatgpt.site/). Deployment `appgdep_6b002589fa488191a3aee79a8f6734b4` succeeded. |
| Version 4 source | GitHub [5bf5d1ad8b8f6c2c1f255f247f4f0880723de902](https://github.com/joedatacap/aidatacenter2/commit/5bf5d1ad8b8f6c2c1f255f247f4f0880723de902), now in main history. Sites commit `2a21859e671f49de6a1951e1c252a3899efa56b2`. A clean rebuild matched all 29 files in that publication. |
| Canonical release on GitHub main | [PR #8](https://github.com/joedatacap/aidatacenter2/pull/8) merged at `128c07d63f2fce67ce654815a17fb4f8fea6ad9d`. PR #9 was retargeted to main. Both review findings were fixed and resolved. [PR #9](https://github.com/joedatacap/aidatacenter2/pull/9) merged at [ff7417ca8851c6488e40514d0a62460c2ae734d8](https://github.com/joedatacap/aidatacenter2/commit/ff7417ca8851c6488e40514d0a62460c2ae734d8). Its Git tree equals the tested PR head `727db69db02b85ec00b8e95397a7fd521c6746fd`. |
| Saved release | Version **5**, Sites commit `2dc216a95a6e4264cc0ae14deb26a287f5edaee6`. Version ID `appgprj_6afb8d8562c0819183402d9c41093312~appgver_65279b0cf1d88191ae8128f565a01e25`. All 29 static files match canonical main. The archive contains those files and the existing hosting manifest. Version 5 has no deployment ID. |
| Data | Cutoff `2026-11-17T18:35:45.406835Z`. In both versions and canonical main, the exact file SHA-256 of `dist/data.json` is `657d5141fe1a8b03e29429954a6829872a8a8c1e600de875eb29dbfb6f2b4838`. The Axe and SharonAI Q3 corrections, fiscal dates, historical scopes and recorded market dates are preserved. |
| Only public asset difference | Version 4 and main match on 28 of 29 files. Main's `watch.js` shows the recorded original and revised milestone windows on the Buildout page and company profiles. All homepage rendering code, route HTML, styles and financial inputs are identical. The other code fix creates the offline output directory on a first custom build. |
| Local build and CI | 179 Python tests, including disposable TLS Postgres, and 74 Watch desktop/mobile browser checks passed locally. [Final PR CI](https://github.com/joedatacap/aidatacenter2/actions/runs/44859523211) also passed 76 legacy and 38 workbench browser checks and all three packaging dry runs. These browser checks exercise built files on a local server and offline. |

**Live verification after both merges.** [Public smoke run 44860376208](https://github.com/joedatacap/aidatacenter2/actions/runs/44860376208) passed ten production checks using desktop Chromium and an emulated mobile Chromium viewport with touch. Both browsers reached the public URL, used the peer checkbox and search, followed a company link and opened source drawers to inspect their links, checked AGPU's buildout stage, exercised chart details, and downloaded and inspected CSV and JSON. The public renderer bytes matched v4 SHA-256 `4a71781cf49a93d45a84e17fe49fe201a4e8edd599cd382dd8bc07497f985279`. Public and main data had the same key-sorted JSON digest `13e3182bc5e5c67dd09765c7bbcd251cbf02670c9c4a3be7df2b54a7f70804bf`. Separately, the linked Axe and SharonAI Q3 SEC filings each returned HTTP 200 with HTML. The workspace proxy itself denied the public site with HTTP CONNECT 403. Production browser results come from GitHub-hosted runners.

The merge left the public version intact. Automatic approval review rejected the subsequent version 5 production deploy because publishing changes the public artifact and the release-check request authorized merges and verification. Resume only upon explicit authorization to **publish saved version 5**. Recheck the version list, successful public deployment and access first. If still current, use the existing saved version ID with step 7's deploy call. A new Site, source push or archive upload is unnecessary.

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
   python scripts/build_neocloud_watch.py --base-path / --output "$stage_dir/dist"
   ```

   Inspect the staged file list and differences, including `data.json`, `audit.html`, `_headers`, assets and all route indexes. The current release has 29 files in `dist/`, including 24 route indexes. For a presentation or packaging change, compare `data.json` byte for byte with the previous publication. When generated files already match, retain the existing deployment.
6. For an authorized publication, update only the existing Sites checkout's `dist/` to match the staged tree. Record the full GitHub SHA in `maintenance/GITHUB_SOURCE.md`. Preserve the hosting manifest and all maintenance history. Verify with `diff -qr "$stage_dir/dist" "$site_checkout/dist"`, setting `site_checkout` to the path opened in step 2. Recheck the remote head and current version before pushing to prevent overwriting another publisher.
7. Follow the Sites source helper to commit, push and package. For a static Git checkout the equivalent archive command is `git archive --format=tar --output=/absolute/path/to/release.tar HEAD .openai/hosting.json dist` from the verified Sites checkout. The archive contains the manifest and generated output. Call `save_site_version` with the same project ID, **pushed Sites commit SHA** and unchanged archive, then `deploy_site_version` with the returned saved-version ID. Keep the existing public audience. If the call is pending, poll `get_deployment_status` until terminal. Verify `get_site` still returns the expected URL, version and access.
8. Run browser smoke checks on the actual public origin from a network that can reach it. On desktop and mobile, check a plotted quarter against the reviewed data, select a peer, open its company profile and a source, and inspect downloaded CSV and JSON. Compare public `/data.json` with the staged file. Record the origin, result and any access error separately from local tests. Update the release receipt with the GitHub SHA, Sites SHA, version, deployment ID, data cutoff, CI and browser results.

### Reproduce the version 4 production browser check

The [release QA revision](https://github.com/joedatacap/aidatacenter2/commit/9a73ca5f6e0c416d712c247a79ece1411ccf0e68) contains the exact Playwright checks and expected version 4 renderer. Use a separate checkout. Install the Python test dependencies as in step 4, then run:

```sh
git fetch origin qa/neocloud-watch-live
git worktree add --detach ../watch-public-qa 9a73ca5f6e0c416d712c247a79ece1411ccf0e68
cd ../watch-public-qa
python -m pip install -e '.[test]'
npm ci
npx playwright install --with-deps chromium
npm run build:watch
env -u WATCH_SMOKE_LOCAL_CONTROL npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

With that variable unset, the test navigations and downloads use the public Sites origin. The test runner also starts a local server for its build control. A run with `WATCH_SMOKE_LOCAL_CONTROL=1` checks local behavior only. When publishing a newer version, use a QA worktree based on its accepted GitHub release commit, carry over the smoke spec, and update its expected renderer fixture using the actual staged `dist/watch.js` for that version. Keep the public target and checks of real interactions intact.
