# Read-only MVP preview

The November 11, 2026 preview adds an immediately usable front end to the existing
NeoCloud financing model. It preserves the original V1/V2 app and Decimal
calculations. No production infrastructure, AIDC site, credentials, database or
runtime research settings are changed.

## Scope

- CRWV, NBIS, IREN, HUT and BTDR company labels; any two can be compared.
- Base, Downside and Tight credit cases; 0/100/200/300 bps benchmark shocks.
- 12/18-month funding gap, funding bars, illustrative equity denominator,
  immediate annualized interest impact, pre-shock coverage and partial maturities.
- Shareable query parameters, pair shortcuts, swap/reset, JSON download.
- A single-file HTML export embeds all assets and data for offline use without a
  server; desktop/mobile browser tests run it with networking disabled.
- Separate historical HUT source excerpts, project coupons and dated principal;
  the revolver commitment is distinguished from unknown drawn balance.
- Desktop/mobile layouts, visible missing-data/error states and keyboard controls.

## Data boundary

`scripts/build_preview.py` exports the existing engine's deterministic results.
There is no separate JavaScript finance implementation. Tests compare every
exported case against Python and verify that HUT project facts are excluded from
synthetic consolidated inputs. Company names identify interface examples, not
estimates. Equal assumptions for some names are intentional. All comparative
funding, equity, cash-flow, hedge and maturity figures are synthetic. The fixture's
scenario date is October 17, 2026; it is not refreshed to today automatically.

The benchmark selector changes immediate annualized unhedged-floating interest.
Tight credit independently changes committed funding treatment and the assumed
future refinancing use. Coverage stays pre-shock. Hedge expiry may change realized
expense; annualization is not a funding-horizon forecast. The UI explains these
boundaries and exports preserve the input/output lineage.

Curated HUT excerpts are retained from the original project and not newly fetched
or re-audited. Market bond yields remain unavailable. This is not a complete
company financial database or an investment ranking.

## Hosting and security

Only HTML, CSS, JS, generated fixture JSON and static response headers ship.
The browser issues no API calls. The preview cannot start investigations, edit
assumptions on the backend, use Crusoe credits or access Neon. The research app's
unauthenticated endpoints are not included. Both Cloudflare configs contain
static assets only, with no custom-domain routes or paid services.

The standalone server uses port 8000. The subdirectory browser test stages files
and uses port 8001. Cloudflare `_headers` restrict scripts and network connections
to the same origin; inline styles are allowed for dynamically sized chart bars.

Cloudflare deployment is **prepared, not performed**. Account access, Free plan,
zone ownership and the narrow route must be verified before deployment. A
Cloudflare dry run does not establish that any public URL exists. No public URL,
live Crusoe investigation or actual Neon persistence is claimed for this build.

## Verification

- Python suite, including exported-case parity: 75 passed; 3 dedicated TLS
  Postgres integration tests skipped without a disposable `TEST_DATABASE_URL`.
- Chromium desktop/mobile interaction tests cover scenarios, horizon/shock changes,
  all company labels, swaps, reset, URL restoration, provenance, downloads,
  missing data, horizontal overflow, JS errors and GET-only static traffic.
- Subdirectory tests verify asset requests remain under `/neoclouddebt/` and the
  host root does not become the app.
- Cloudflare Static Assets dry runs validate both standalone and subpath bundles;
  no deploy command runs in CI.

Screenshots and Playwright output are retained under ignored `work/` locally and
uploaded as CI artifacts. CI does not publish or deploy the app.

Review fixes also validate inherited object names (`__proto__`, `constructor`,
`toString`) in either shared-link ticker parameter. They fall back independently
to supported tickers. Small eyebrow labels now have at least 5.04:1 contrast on
their actual backgrounds. Keyboard focus outlines use different colors on light
content and dark header/footer backgrounds; tests require at least 3:1 contrast
and a visible 3px outline. All 14 desktop/mobile browser checks pass locally.
