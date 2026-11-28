# Existing-call audit — November 27, 2026

Information cutoff: **2026-11-27 09:00 UTC**. This is a bounded review of current source-backed calls, not a fresh set of nine price targets or continuous monitoring. The machine-readable audit is `neocloud/data/underwriting/audit.json`. No historical report, rating, price or immutable snapshot was changed.

A verdict tests the concrete financial/delivery claim identified in that row. `support` means a primary disclosure supports that claim; `partial` means the factual premise is supported but a material financial inference remains conditional. Neither means an investment recommendation, technical objective or fair value has been independently validated. Unknown future cash is not zero.

## Which calls actually exist

The nine calls being audited are dated November 26, 2026. The new NBIS and CRWV calls appear separately in the November 27 underwriting edition. Only CRWV, APLD and AGPU have separate 30–90 day tactical Justin cards: rating Hold, displayed as **Hold existing / Wait new**, low confidence. Their $48, $14.20 and $7.91 tactical retest objectives are conditional technical objectives, not twelve-month valuation targets. A filing cannot by itself validate those price levels.

NBIS has the twelve-month **Hold** call. IREN has **Watch / financing- and acceptance-dependent**, not a conventional Buy/Hold/Sell call. HUT, WULF, WYFI and SHAZ remain **Under review**: no directional rating or twelve-month price target. APLD also remains Under review on the fundamental page despite its distinct tactical Hold card. Do not backfill a missing fundamental rating from a tactical card.

The current report and archived November 26 versions were inspected together. Archive IDs below preserve the distinction between tactical and fundamental reports:

| Company | Archived report version |
|---|---|
| CRWV tactical | ddfeb6ba706c418000cee5c656f669ca1eb456d790113002ebbf4b1f3f9e1363 |
| CRWV fundamental | b0530b59ccea37ea98d31ff1851ed00921f5a4c9a1d46cfc2681a3a6ee2b0f93 |
| NBIS fundamental | 31deb9cfe250501e3c22c0ae0a0eb89119487b6c456aea413f7bc5e9456c62ec |
| IREN fundamental | 90b327b29e0c459f777cf760b9c70b714dabec77db0e7941fc47f956eb3e61b8 |
| APLD tactical | 8256a0c3c84aea2265044764911ba59e33825a9442249af2b6486dadd6dd2f1e |
| APLD fundamental | edf4cf991888b00299ace95ab3117cdb9b84b54293b62fa99b3269ad89ecc1d7 |
| HUT fundamental | 7e3c9ec08f6e2406a16c18f97d29f7688a273b2fb54c74daf359adb878dd2987 |
| WULF fundamental | d3ebc447bf56677146eb324892c939c3235fe1507cf18aca5121b98fd10cfa18 |
| WYFI fundamental | c44f1b90332087ea21fc8b1a08cec4d34cee2376559ddf8f44d949a0ebb75f5d |
| SHAZ fundamental | 76c600cafe17b09b2aefa648eacea5cd01f781fecbc7743c11e350184904a9d0 |
| AGPU tactical | 101388874bc4b3d8ccb74ee12f123cfb1ea6676a9685d979ea439d6aead7e1a9 |
| AGPU fundamental | 26fc661ca2586259358f4ee11b7b274e5aad064dc45a8795bbf2c9db6af74d67 |

Files reside under `neocloud/data/equity-history/versions/{ticker}/{version}.json`. November 26 fundamental inputs are in `neocloud/data/equity/`; tactical inputs are in `neocloud/data/justin/`.

## Filing freshness and scope

The nine issuers' recent SEC filings were screened against retrieved November 17–25 daily master indexes, with direct primary-document review of the material financing/capitalization items. Latest reviewed indexes include [November 24](https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/master.20261124.idx) and [November 25](https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/master.20261125.idx). November 26 was Thanksgiving and the cutoff precedes the November 27 ordinary filing acceptance window. A November 26 index access attempt was denied; absence of an accessible index is not independently a no-filing certificate. This review does not claim an exhaustive real-time feed or access to private financing records.

The latest material items found before cutoff were already published before the current November 26 call date:

- **APLD, November 24 8-K:** [primary filing](https://www.sec.gov/Archives/edgar/data/1144879/000149315226054002/form8-k.htm). The Series G PEPA commitment increases from $2B to $2.5B; the filing states **$1.035B remaining availability**, rather than $2.5B of fresh cash. It also furnishes the November 23 announcement of a new eighteen-year, 150 MW critical-IT lease and a subsidiary bridge-facility closing. An executed facility, funded cash, commissioned capacity and rent recognition remain separate observations.
- **SHAZ, November 24 amendment / November 25 prospectus supplements:** [primary supplement](https://www.sec.gov/Archives/edgar/data/2068385/000149315226054224/form424b3.htm). The supplemental indenture removes the restriction on repayment of indebtedness under the 4.75% June 2032 notes and aligns related provisions with the 6.00% 2031 notes. This is a covenant change, not proceeds or proof of the entire construction funding bridge. Other November 25 424B3 filings are not four independent cash raises.
- **AGPU, November 24 DEF 14A and ARS:** [proxy](https://www.sec.gov/Archives/edgar/data/1446159/000117184326007694/agpu20261122_def14a.htm). The December 17 meeting proposes additional incentive-plan authorization. The annual-report filing is not a new September-quarter earnings report. Neither establishes a completed Georgia customer-acceptance event.
- November ownership filings and Forms 144 are not treated as corporate cash issuance, new operating earnings or proof of a funded construction tranche. No new accepted-customer/billing or project-completion fact was inferred from calendar passage.

The company rows cite the dated primary source that supports each concrete claim, with the filing table/note or release section as locator. Current company-specific evidence gaps remain explicit, especially future receipts, actual draws, acceptance and fully diluted shares. IR releases included or linked by SEC filings remain issuer assertions; capacity and guidance stages retain their qualifications.

## AGPU economic-share check

[September 30 Form 10-Q, filed November 17](https://www.sec.gov/Archives/edgar/data/1446159/000117184326007507/agpu20260930_10q.htm) is the primary capitalization and operating source. The November 24 proxy provides a later record-date/legal-share observation and award-plan proposals.

| Item | Observation | Treatment |
|---|---|---|
| September 30 legal common | 13,634,097 | Legal shares only. |
| September 30 prefunded warrants | 7,736,379, $0.01 exercise price | Economically relevant claims; do not omit because basic-market-cap providers do. |
| Same-date common plus prefunded | **21,370,476** | Calculated partial economic denominator, not fully diluted shares or a current quote-date capitalization. |
| Q3 weighted-average basic EPS shares | 21,370,333 | Period average; not point-in-time capitalization. |
| November 13 cover common / November 6 proxy common | 13,650,314 | Later legal common. Do not add an unchanged September prefunded balance without reconciling intervening exercises. |
| September other warrants | 1,592,749, weighted exercise price $12.53 | Separate from prefunded warrants; common-equivalent treatment requires terms and price sensitivity. |
| September options / later proxy options | 1,322,883 / 1,422,883 | The later count includes 100,000 October inducement options; vested/unvested subtotals must not be added twice. |
| Series B preferred | 79,246 preferred shares | Not presumed one-for-one common. Conversion/dividend/redemption rights require explicit reconciliation. |
| Proposed additional plan reserve | 2,000,000 shares, proposed total 3,066,667 | Authorization proposal at December 17 meeting, not completed issuance. A future evergreen is not current shares outstanding. |

The [June 2026 Form 10-Q, Reverse Stock Split section](https://www.sec.gov/Archives/edgar/data/1446159/000117184326005556/agpu20260630_10q.htm) confirms the 1-for-15 split completed September 29, 2025 and became effective for trading September 30, 2025; the reported share/per-share data were already adjusted. Do not apply another factor of fifteen. Current fully diluted capitalization remains unresolved. Dated provider basic market cap may be shown separately with its denominator/date caveat; it must not be substituted for an audited current economic claim value or used to establish a reliable dilution-adjusted upside percentage.

Operationally, energized/provisioned Georgia hardware, customer acceptance, recognized Build revenue and collected cash are separate stages. The November 17 release retains the Q4 2026/Q1 2027 acceptance/service-entry window; calendar passage before that window closes is not a verified new delay. Q3 reported operating income of $6,825,897 less digital-asset gains of $10,477,971 equals **−$3,652,074**; that arithmetic isolates one accounting item and is neither cash flow nor an issuer adjusted-EBITDA measure. The $364.6M amended lifetime contract is not current annual revenue, collected cash or free cash to common.

## Ranked next work among the other seven

1. **APLD — project cash to common.** Reconcile remaining construction and debt service to TopCo 2 distributions, Macquarie claims and Series G draw/conversion terms. The key decision is how much consolidated cash and signed rent can reach each common share, and when.
2. **AGPU — accepted cash economics per economic share.** Close a same-date share-count/prefunded roll-forward, then reconcile Georgia acceptance and cash gross margin against customer obligations, seller/debt payments and hardware replacement. A basic-cap shortcut can change the investment conclusion.
3. **SHAZ — quarter-by-quarter committed construction funding.** Map the $5.35B commitment scope to dated receipts, actual facility draws, guarantees and service commencement. Separate RPO conversion from financing proceeds and identify the equity needed before cash can reach common.

These priorities supplement the separate NBIS and CRWV deep dives. They do not assign new ratings or invent targets for the remaining seven.
