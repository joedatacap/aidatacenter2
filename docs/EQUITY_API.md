# NCW research API v1

Build the normal Watch site with `PYTHONPATH=. python scripts/build_neocloud_watch.py`. At the site root, open `research/` for Justin's investment brief or `api/v1/` for the browsable endpoint catalog. A standalone offline edition is generated at `work/NCW-Equity-Research.html`. Build inputs are reviewed JSON records, and the public site requires no database credentials or running Python service.

## HTTP resources

Use GET on the canonical paths. JSON MIME type is determined by the .json extension. The static Cloudflare redirects manifest additionally maps the extensionless forms. A plain static file server supports the .json paths. The JSON envelope contains schema_version, edition and data. Company symbols are uppercase. Unknown canonical resources return the host’s file-not-found response.

| Resource | Contents |
|---|---|
| /api/v1/index.json | Discover all resources |
| /api/v1/overview.json and /api/v1/companies.json | Dates, cohort, benchmark identities, coverage and ticker index |
| /api/v1/companies/NBIS.json | Complete company package and source registers |
| /api/v1/companies/NBIS/{financials,financing,contracts,valuation,events,audit}.json | Separate company collections; substitute any covered ticker and one section |
| /api/v1/market/history.json | Approved downloadable bars, identity and benchmark audits; empty when rights or data are missing |
| /api/v1/justin/research.json | Nine investment reports with separate tactical editions, sources, caveats and conflicts |
| /api/v1/justin/history.json | Immutable edition hashes, timestamps, original call, price objective and release status |
| /api/v1/justin/scorecard.json | Versioned, forward-only comparisons and pending reasons |
| /api/v1/events.json | Monitored disclosures, channel health, changes and review status |
| /api/v1/snapshot.json and /api/v1/snapshot.md | Consolidated machine-readable and human-readable snapshots |

## Reproduce comparisons

Issuer-reported actuals retain original periods, currency, units, attribution and source IDs. The financials resource distinguishes reported actuals, management guidance, external consensus status and Justin's independent models. Model outputs are USD millions per fiscal year. Contract bridges may only cover part of the business. A missing consolidated number is null. Model input changes require recalculation and passing arithmetic tests before release.

Common equity uses the reviewed reference close and the most recent reconciled common count. Same-date common plus nominal-exercise warrants is disclosed separately where available. A fully diluted count is withheld without a current bridge. Indicative EV uses available claim balances, retaining consolidated nonrecourse debt within consolidated EBIT/EBITDA scope. It uses book preferred/minority balances where measurable. Reported finance leases are added once. A missing claim blocks the complete bridge. The partial bridge explicitly omits minority/preferred claims. Check each issuer's note for cash restrictions, accounting differences and post-quarter financing. Forward multiples compare the dated bridge against modeled financials. P/E requires positive earnings attributable to common; EV/EBITDA requires a positive, comparable denominator. Signed FCF yield can be negative.

Source IDs resolve locally in sources, watch_sources or the audit source register. Dates describe distinct events including period end, publication, last verification and edition. Third-party editorial references do not grant permission to redistribute historical price series. No consensus license or paid price service was purchased. Public exports are built from reviewed repository inputs. The separate infrastructure database and private user journals are outside this projection.

## Versioning

Investment drafts, publications and subsequent outcomes are distinct. Official public release notices attach to an exact immutable hash. Edited calls produce new records. Use scorecard status and matched dates before quoting any performance. The event monitor queues review candidates; subsequent model changes need supporting public evidence and a new edition.

`GET /api/v1/peers.json` returns the nine-company operating comparison shown on the research overview. Each member includes its selected contract stage and sources, statement date, modeled fiscal period, indicative EV/base-revenue multiple or reason withheld, and eligibility for the dated QQQ and NVDA comparison. Eligibility requires matching endpoint dates, currency and adjustment basis and a return reproducible from the reviewed endpoints. Display-only market observations stay in attributed editorial views. The consolidated JSON and Markdown downloads also include the operating comparisons.

The four-company decision brief is at `research/decisions/`. Use `api/v1/justin/decisions.json` or `api/v1/justin/decisions.md` for the downloads. The dated resource `api/v1/justin/decisions/2026-11-27.json` identifies the saved preview edition. Each row references its investment archive version. NBIS and CRWV conditional values link to the pinned funding study. Firm targets, preview recording time and public release time have separate fields. Reference prices are attributed in HTML and linked in downloads.
