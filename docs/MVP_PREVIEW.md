# Read-only preview and preserved scenario lab

The default preview now opens the **16-company source-backed borrowing
directory**, described in [DEBT_DIRECTORY.md](DEBT_DIRECTORY.md). The synthetic
five-company lab documented below is preserved separately at `/scenarios/` and
in `work/NeoCloud-Scenario-Lab.html`. Its assumptions never enter actual ranks.

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

- Python suite, including directory validation and exported-case parity: 116 passed; 3 dedicated TLS
  Postgres integration tests skipped without a disposable `TEST_DATABASE_URL`.
- Chromium desktop/mobile interaction tests cover scenarios, horizon/shock changes,
  all company labels, swaps, reset, URL restoration, provenance, downloads,
  missing data, horizontal overflow, JS errors and GET-only static traffic.
- Directory browser checks additionally cover actual company ranks, peer groups,
  source dialogs, borrowing reconciliation, coupon-reference separation, genuine
  zero coupons, unknown balances, dated source lineage and standalone operation.
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
and a visible 3px outline. The complete suite now covers 66 desktop/mobile browser checks across both apps.
Directory checks include three-company comparisons, nested-dialog focus, note
type/status filters, stable cohort ranks during search, principal/lease context,
private-issuer labels and the unranked private-operator coverage watchlist.


## First-use reading guide

The default directory has a closed-by-default “New here?” walkthrough. Three
steps explain recorded/book borrowing balances versus contractual principal,
assets versus spendable cash, and coupon versus market yield. A boxed arithmetic
example is explicitly labeled as made up, not a company estimate. Actions open
the relevant metric without clearing the visitor's peer group, text search,
note filters or sort order. They move keyboard focus to the figures. A separate
action names the first visible company and opens its actual source panel;
Escape returns focus to that button. Empty results and failed datasets cannot
open a fabricated company example. No forced tour or saved personal state is used.

Source review now includes an explicit unique-URL coverage map. The optional DLR
finance-lease amount became unknown after independent SEC follow-up could not
support a presentation-derived figure. Its SEC-backed borrowing subtotal and
operating-lease disclosure remain unchanged.


## Cash and funding context

Company evidence and side-by-side comparisons distinguish reported group cash,
restricted balances, nominal commitments, outstanding borrowing, reported unused
capacity and explicit facility availability. Twenty-one selected facilities are
shown across the 16-company directory. This is not a complete inventory, so no
company-wide available-credit total or cash-plus-credit figure is calculated.
Cash qualifications and nested facility details survive JSON/CSV downloads;
CSV stores the nested liquidity object as JSON in one escaped cell.

The validator requires same-snapshot USD evidence and explicit access conditions,
rejects synthetic funding inputs and prevents restricted balances or credit
capacity from being treated as cash. Later financing and amendments do not update
earlier cash snapshots. Digital Realty's obsolete 'unreviewed coupon' drafting
text was also removed from the UI and exports, with regression coverage.


Source-reading polish replaces numeric-token excerpt summaries with short,
mechanically checked labeled passages or clearly identified table cells, including
units and comparison-column dates. Empty note examples show Unknown with a
specific reason; internal principal-scope codes are translated in the display.
Historical references do not imply that omitted financing records appear on screen.
A fresh IREN filing request succeeded on November 11 at 10:27 UTC and reconfirmed
its three conditional unused commitments. The earlier independent reviewer's
access failure remains documented; one successful request does not guarantee
that every reviewer can access the filing.


## Direct cash and funding view

A fourth tab and a main-navigation link expose reported cash and separate facility
amounts without opening a modal. Every row also has a Cash & funding action.
“Total not established” is accompanied by reviewed-facility counts and sourced
conditional/available/LC-only amounts, never a sum. Company takeaways are factual
and source-backed. Sort labels name the actual measure; cash profiles have no
ordinal ranks or bars. Repeated meanings and full cash restrictions use native
expandable details. Navigation and row actions work with keyboard and offline;
closing the evidence dialog restores the initiating action's focus.
