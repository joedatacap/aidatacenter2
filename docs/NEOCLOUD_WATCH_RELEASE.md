# Neocloud Watch release and publication

The public site is [Neocloud Watch](https://neocloud-watch.gpuchips.chatgpt.site/). GitHub `joedatacap/aidatacenter2` on `main` is the application source. ChatGPT Sites stores the generated static publication in its own source repository on `main`. A GitHub merge runs tests and packaging dry runs. Publication is a separate operation.

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
