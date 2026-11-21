# Public Neocloud Watch smoke verification

This temporary QA branch adds read-only public-browser checks to the existing Watch Playwright suite. The only site target is the fixed public URL `https://neocloud-watch.gpuchips.chatgpt.site/`. No credentials, environment-specific proxy overrides or deployment operations are used. Source drawer links are inspected, not followed to unrelated external sites.

The unchanged existing GitHub Actions workflow runs these tests on branch push, alongside the existing local suites. It compares the public `data.json` against the canonical generated snapshot by recursively key-sorted SHA-256, compares public `watch.js` byte-for-byte with the checked-in v4 fixture generated from `5bf5d1ad8b8f6c2c1f255f247f4f0880723de902`, checks Axe original/revised target windows and customer acceptance on the homepage tracker, and exercises public desktop/mobile charts, the Selected peers checkbox, shared peers/search/navigation, refresh, source drawers, JSON/CSV downloads, exact Axe figures, keyboard/tap details and overflow. Live screenshots use `work/watch-live-*.png` and are included in the workflow's existing artifact upload.

Run manually after building the canonical snapshot:

```sh
npm ci
npm run build:watch
npx playwright install chromium
npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

The data baseline is merged main `ff7417ca8851c6488e40514d0a62460c2ae734d8`. The renderer baseline is deployed v4 `5bf5d1a`; main has an unshipped company Buildout profile target-window fix. This smoke intentionally makes no claim that the public renderer equals main. For a future separately authorized publication, regenerate the fixture from that approved release commit by replacing the single `/* @include overview-charts.js */` marker in `watch-preview/watch.js` with the contents of `watch-preview/overview-charts.js`, exactly as the build script does, then rerun the QA Actions run. If canonical code/data changed, create a new isolated QA branch from the new canonical commit, carry over `tests/browser-watch/public-live.spec.cjs` and this receipt, then push it to trigger the existing workflow. Do not modify or merge the feature/release branch merely to run this smoke test. No workflow YAML edit is required.

A runner HTTP/DNS/TLS failure, unavailable application shell, mismatched data digest or failed public interaction remains a failure. It is not converted to a skip or labelled successful publication.

Local control against the exact branch build uses only the fixed localhost preview address and is explicitly labelled `local_control` in the receipt:

```sh
WATCH_SMOKE_LOCAL_CONTROL=1 npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

This checks selector correctness; it is never evidence of a successful public request. Normal CI leaves this variable unset and contacts only the fixed public site.
