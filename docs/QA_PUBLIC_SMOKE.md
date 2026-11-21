# Public Neocloud Watch smoke verification

This temporary QA branch adds read-only public-browser checks to the existing Watch Playwright suite. The only site target is the fixed public URL `https://neocloud-watch.gpuchips.chatgpt.site/`. No credentials, environment-specific proxy overrides or deployment operations are used. Source drawer links are inspected, not followed to unrelated external sites.

The unchanged existing GitHub Actions workflow runs these tests on branch push, alongside the existing local suites. It compares the public `data.json` against the canonical generated snapshot by recursively key-sorted SHA-256, compares public `watch.js` and `data.json` byte-for-byte with the generated main-built v5 assets, checks IREN, HUT and NBIS target windows on both the full Projects page and their company profiles, and Axe target windows/customer acceptance on the homepage tracker, and exercises public desktop/mobile charts, the Selected peers checkbox, shared peers/search/navigation, refresh, source drawers, JSON/CSV downloads, exact Axe figures, keyboard/tap details and overflow. Live screenshots use `work/watch-live-*.png` and are included in the workflow's existing artifact upload.

Run manually after building the canonical snapshot:

```sh
npm ci
npm run build:watch
npx playwright install chromium
npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

The v5 baseline is main `4f45fecbf0248cfbb29356ad98474bbe040890e4`, deployed as `appgdep_6b01b75857948191ae1afe54423c2867`. The public verification must match this generated renderer and snapshot exactly. The older v4 fixture is historical evidence only and is not used by v5 tests. For a future separately authorized publication, synchronize this isolated QA branch with the approved release commit and run the same checks. Do not modify or merge the release branch merely to run this smoke test. No workflow YAML edit is required.

A runner HTTP/DNS/TLS failure, unavailable application shell, mismatched data digest or failed public interaction remains a failure. It is not converted to a skip or labelled successful publication.

Local control against the exact branch build uses only the fixed localhost preview address and is explicitly labelled `local_control` in the receipt:

```sh
WATCH_SMOKE_LOCAL_CONTROL=1 npx playwright test --config playwright.watch.config.cjs public-live.spec.cjs
```

This checks selector correctness; it is never evidence of a successful public request. Normal CI leaves this variable unset and contacts only the fixed public site.
