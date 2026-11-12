# NeoCloud Debt Intelligence: handoff to the next GPT or Codex chat

Updated November 12, 2026. Repository: https://github.com/joedatacap/aidatacenter2

## Start here

Joe wants to continue this project in a separate GPT or Codex chat. Attach this
document or give the next agent its GitHub link. Prefer a visible Codex project
with this repository attached, so Joe can see progress and steer the work.

Suggested opening prompt:

> Continue NeoCloud Debt Intelligence in joedatacap/aidatacenter2. Read AGENTS.md,
> README.md and docs/HANDOFF.md, inspect the actual main branch, PR #7 and latest
> CI/deployment state, then explain the current product before changing it.
> Preserve the financial evidence and missing-data boundaries. The intended
> production hostname is neoclouddebt.datacap.xyz. Keep hosting on Cloudflare Free,
> expose only the static read-only app, and preserve all unrelated sites. Never
> invent company averages, market yields, debt balances or a health ranking.

GitHub is the durable source of code and evidence. An earlier chat's summary,
local work directory, screenshot or pending CI run is not proof of deployment.
Check the release status below and recheck live state before acting.

## Release status

- MVP PR: https://github.com/joedatacap/aidatacenter2/pull/7
- Product implementation head before release fixes: `bbab6e351a609a7939a904649bdb4fe5aa5daa47`.
- Release fixes pin CI to Ubuntu 24.04 and retain Chromium-install diagnostics.
  Earlier CI failed in `npx playwright install --with-deps chromium`, before
  browser tests ran. `ubuntu-latest` migration was flagged by GitHub; exact
  installer error could not be read because log download was denied. OS pinning
  removes runner drift; the next CI result, rather than inference, establishes
  whether this resolves the setup failure.
- Production config: `wrangler.production.jsonc`, only
  `neoclouddebt.datacap.xyz`, static assets from `preview/`, no backend/bindings,
  no workers.dev or preview URL. Do not use the old subpath target by accident.
- **Publishing is blocked at handoff preparation:** no Cloudflare API token or
  account ID is configured in this Codex environment. No Cloudflare account,
  zone ownership, existing hostname mapping or Free-plan status has been verified.
  GitHub secret/variable metadata queries returned HTTP 403. The environment's
  proxy denied HTTPS to the intended hostname. No deployment was attempted.
- Merge, CI and publication outcomes must be updated in the final release receipt
  below; do not interpret this preparation section as a successful release.

## Product and user intent

A light, useful demo comparing financing behind GPU clouds and AI infrastructure.
Joe found recorded borrowing dollars useful and explicitly requested the asset
percentage beside them and understandable financing rates. The US data-center
map idea was abandoned. Avoid turning this back into a large research platform
before the simple comparison is useful.

The default directory covers 16 companies: CRWV, NBIS, IREN, BTDR, HUT, APLD,
CORZ, WULF, CIFR, HIVE, GLXY, RIOT, MARA, EQIX, DLR and Nscale. Peer filters
separate GPU clouds, mixed businesses, miners and REITs. Fifteen have comparable
borrowing totals and asset ratios; Galaxy's total is unresolved and unranked.
Nscale is a private IPO applicant with public financials, not a verified listed
stock. Crusoe, Lambda and Vultr are a separate unranked coverage watchlist.

Four views:

1. Borrowing carrying amounts, excluding all operating and finance leases.
2. Same-date borrowings / recorded assets. Main borrowing rows also show the
   actual percentage and a fixed 0–100% asset meter with expandable denominator,
   snapshot and publication dates. CoreWeave's reviewed example is
   $46.873B / $91.481B = 51.24% at September 30, published November 10, 2026.
3. Financing rates: unranked company references plus a separate 44-note USD
   fixed-coupon ledger. There are 36 typed references across 15 companies.
4. Cash & funding: unranked reported cash plus 21 selected facility disclosures.
   Conditional unused credit, reported availability and LC-only headroom stay
   separate. Company-wide available credit reads “Total not established.”

Users can compare up to three companies, search without changing peer-cohort debt
ranks, inspect sources, share query parameters and export JSON/CSV. A standalone
HTML embeds the same app and evidence for offline use.

## Architecture and files

| Area | Source of truth / purpose |
|---|---|
| Actual directory | `neocloud/data/debt_directory.json` |
| Validation and Decimal calculations | `neocloud/directory.py` |
| Generate browser data | `scripts/build_debt_preview.py` → `preview/data.json` |
| Static UI | `preview/index.html`, `preview/preview.js`, `preview/preview.css` |
| Static security headers | `preview/_headers` |
| Offline build | `scripts/build_standalone.py` → ignored `work/NeoCloud-Interactive-Preview.html` |
| Preserved synthetic lab | `preview/scenarios/`, separate offline scenario HTML |
| Browser tests | `tests/browser/directory.spec.cjs`, `preview.spec.cjs`, `playwright.config.cjs` |
| Python tests | `tests/test_directory.py` and existing runtime/finance suites |
| CI | `.github/workflows/test.yml`, disposable TLS Postgres, browsers, dry runs |
| Production target | `wrangler.production.jsonc` |
| Older deployment preparations | `wrangler.jsonc`, `wrangler.subpath.jsonc`, `scripts/stage_preview.py` |
| Methodology and audit receipts | `docs/DEBT_DIRECTORY.md`, `docs/DIRECTORY_*` |
| Original runtime | `neocloud/` Python FastAPI research app, V1/V2 engines and Neon adapters |

The public static build makes no API/inference/database calls. The existing
Python backend includes unauthenticated operations and must not be exposed by
this deployment. The static HTML contains source-backed snapshots; it is not an
autonomous live data feed. Original runtime research uses Crusoe, not separately
billed OpenAI API calls. Keep the existing Neon database adapters; production
Neon persistence has not been independently established by this MVP deployment.
Do not replace the database or deploy the Python process onto Workers as-is.

## Evidence and financial boundaries

The November 11 ledger has 131 source records across 54 unique URLs. Financial
dates vary (principally September 30, with NBIS/Nscale June 30 and APLD August 31).
This is a curated historical snapshot, not today's balance sheet or current yield.
Sources include primary SEC filings and official issuer disclosures. Material
records retain dates, currency/units, instrument/borrower/scope, supporting
excerpts and evidence status. Start with `docs/DEBT_DIRECTORY.md` and the source,
note, remaining-source, liquidity and financing-rate review JSON receipts.

- Borrowing carrying value is not face principal, all liabilities, funding
  availability or repayment capacity. Preserve lease exclusions and other
  liabilities, especially Nscale's substantial deferred customer revenue/leases.
- The meter is percentage of recorded assets, not peer size, health or a claim
  identifying which assets debt funded. Unknown or mismatched-date inputs get no
  meter; over-100% values keep their full number while the visual caps at 100%.
- Only APLD (7.3%, term-loan portfolio) and DLR (3.07%, a consolidated borrowing
  table with designated swaps and different scope) have issuer-reported averages
  in the ledger. They are not uniformly comparable all-company effective costs.
- Named note coupons, fixed contractual loan rates, floating formulas, reported
  variable rates and accounting effective rates are different types. Never blend
  them or infer a full-company weighted average/most expensive tranche from an
  incomplete inventory. An accounting effective rate is not the cash coupon.
- Floating formulas preserve benchmark and spread in percentage points. Without
  a sourced fixing value/date, all-in rates remain unknown. CoreWeave's DDTL5.5
  example is dated original terms, not a verified current borrowing cost.
- The proposed CoreWeave 7.9% average remains an unverified research lead. Its
  official transcript PDF was denied by the environment proxy; omit it until a
  readable primary source establishes value, date, scope and method. Do not retry
  a denied route through another mechanism to evade the policy.
- Commitments, drawn amounts, balances, conditional availability and LC sublimits
  are distinct. No cash-plus-credit sum, invented liquidity total or health score.
- Historical coupons need not still be outstanding. Zero convertible coupons
  carry equity-option economics and do not mean free financing. Project debt and
  guarantees do not automatically apply to the whole company.
- New filings must be reconciled before refreshing a company's snapshot. Do not
  mix later loans with earlier assets. Synthetic lab inputs never enter actual ranks.

## Local development and verification

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
npm ci
.venv/bin/python scripts/build_debt_preview.py
.venv/bin/python -m pytest -q
npx playwright install --with-deps chromium
npm run test:preview
npm run build:standalone
npm run deploy:dry-run
npm run deploy:subpath:dry-run
npx wrangler deploy --config wrangler.production.jsonc --dry-run
```

If Chromium is already installed, use
`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run test:preview`.
Tests start static servers on 127.0.0.1 ports 8000 and 8001; avoid stale servers
serving older files. `npm run preview` serves only `preview/` on port 8000.
The scenario runtime and actual directory have distinct fixtures and tests.

The product head passed 131 local Python tests with three dedicated disposable
Postgres tests skipped, and all 76 desktop/mobile browser checks. CI supplies a
dedicated TLS Postgres URL and must pass those database checks too. Never point
destructive integration tests at the real production `DATABASE_URL`.

## Publishing runbook and access blockers

Joe authorized fixing tests, merging PR #7 if appropriate, and publishing this
static version to **neoclouddebt.datacap.xyz**. Earlier no-merge/no-deploy limits
were superseded for this specific release; paid services remain unauthorized.

1. Inspect PR head/checks/reviews and latest main. Merge only the tested intended
   head with an expected-head guard; never bypass branch protection or use admin
   override. Keep the feature branch until deployment/rollback is established.
2. Configure `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` securely in the
   environment (never chat, frontend, repository, logs or handoff). Use a token
   scoped to Workers Scripts Edit and the necessary datacap.xyz zone access for
   Workers custom domains. Verify the selected account and active managed zone.
3. Allow HTTPS to `api.cloudflare.com` and `neoclouddebt.datacap.xyz` in the
   execution environment. The former was allowed; the latter was denied at
   handoff preparation. A permission change must be applied before a fresh probe.
4. Before writing, inspect existing Workers, custom-domain assignments, DNS and
   Workers plan. Confirm `neocloud-debt` and the hostname are absent or belong to
   this app. If occupied by another site, stop and resolve ownership. Record any
   existing intended-app version before replacement. Do not delete existing DNS
   records or change `aidc.datacap.xyz`, the apex or any wildcard route.
5. Confirm Free/static-only operation and the checked-out merged commit. Rebuild
   and dry-run `wrangler.production.jsonc`, then execute:

   ```sh
   npx wrangler deploy --config wrangler.production.jsonc
   ```

   Wrangler custom domains cover this exact hostname. No backend, secrets,
   inference, database bindings or additional billing plan belongs in this build.
6. Record the deployment/version ID and exact source commit. Verify HTTPS root,
   JS/CSS/data, company counts, CRWV percentage, rates, cash, queries and downloads
   in desktop/mobile browsers. Check browser console/network, headers and no API
   calls. Confirm `/api/` does not expose the Python app. Verify unrelated routes
   remain unchanged using before/after checks where access is permitted.
7. If deployment fails or its outcome is uncertain, inspect provider state before
   retrying. A denied call is not permission to use an alternate credential,
   network route or tool. Distinguish “not attempted,” “denied,” “deployed but
   verification blocked” and “verified live.” Update this handoff with evidence.

Rollback an existing app using the provider's recorded previous deployment ID,
after reviewing what changed. For a first deployment, remove only the new app's
exact domain mapping if rollback is necessary and authorized; preserve all other
DNS, Workers and sites. Do not improvise broad zone changes.

Official references: [Cloudflare custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/),
[static assets](https://developers.cloudflare.com/workers/static-assets/), and
[Playwright CI](https://playwright.dev/docs/ci).

## Next useful work

1. Complete verified publication once access is configured; update the release
   receipt with real merge SHA, CI links, deployment ID and live browser results.
2. Watch Joe use the simple demo. Prioritize readability of the borrowing dollars,
   asset percentage and named rate rather than adding many features.
3. Reconcile newer filings as whole snapshots, starting with companies whose
   next results follow the snapshot cutoff. Keep an explicit reviewed-at date.
4. Resolve Galaxy borrowing scope, Bitdeer rate coverage and private-operator
   disclosure gaps only where reliable comparable evidence exists.
5. If adding live research, design authentication, rate limits and budgets before
   enabling POST operations. Prove actual persistence and bounded runtime behavior
   separately; static publication does not prove these work.

## Final release receipt

Pending completion of release checks. Publishing remains blocked by missing
Cloudflare credentials and target-host network access unless superseded by a
dated verified receipt added here. No credential values belong in this document.
