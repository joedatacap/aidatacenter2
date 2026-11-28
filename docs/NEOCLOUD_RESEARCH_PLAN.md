# Neocloud research plan

Updated November 28, 2026. Use [issue #30](https://github.com/joedatacap/aidatacenter2/issues/30) to track decisions, release status and new observations. Edit this document when priorities, evidence or criteria change.

## Decisions and delivery

| Workstream | Decision or result | Next observation and action |
|---|---|---|
| [Nebius financing tests](NBIS_FINANCING_TESTS_2026_11_28.md) | Hold / high risk at the November 25 close. Favorable guidance yields $112.14 but 29.55% dilution. Delayed advances reduce value to $87.13. | Refresh actual dated advances, eligible collateral, lender draws and equity proceeds. Reopen the call when at least 25% upside and at most 25% dilution are supported, with New Jersey execution evidence. |
| [CoreWeave financing tests](CRWV_FINANCING_TEST.md) | Hold existing at the November 25 close. A one-quarter deposit delay adds $6B to immediate net equity. Reducing post-replacement cash conversion to 50% gives $28.48. | Reconcile collections to deferred revenue and eligible loans. Estimate GPU replacement spending from a mature fleet. Rerun against the 30% upside hurdle. |
| [Applied Digital project cash](APLD_PROJECT_CASH_2026_11_27.md) | Fundamental call stays under review. At Oracle-backed Harwood, illustrative stabilized midpoint NOI less initial interest and principal leaves $39.85M annually at the project. Distribution to common is unknown. | Track accepted MW and actual rent, cash reserve releases, preferred distributions, parent overhead and common shares. Reconcile the first disclosed project distribution to the parent. |
| [Eleven-issuer credit review](NEOCLOUD_CREDIT_REVIEW.md) | Use a facility-specific cost for identifiable borrowing. Date and classify each market observation before using it. | Refresh in-market packages when a signed agreement, rating or closing arrives. Prioritize Dalton, Delta Forge 1, the CORZ and WULF financings, and AGPU's Georgia refinancing. |
| Release | Integrate #29 into #27, run combined checks, merge into main, publish both dated reports to the existing Neocloud Watch site. | [Issue #30](https://github.com/joedatacap/aidatacenter2/issues/30) carries the release receipt and any outstanding items. PR #28's separate 100 MW delivery sensitivity can advance independently. |

## Research queue

1. **Axe Compute.** Reconcile a single-date economic share count, cash received after Georgia acceptance, compute supplier payments and the seller balance. Establish cash margin attributable to common shareholders before setting a per-share target.
2. **SharonAI.** Trace each announced capex commitment to cash on hand, customer receipts or a drawable financing line. Quantify any gap by date and identify which obligations can be deferred.
3. **Credit data refresh.** Capture instrument ID, obligor, collateral, pledged offtake, guarantee scope, cash controls, advance rate, maturity, amortization, fees, rating, status and source. For market quotes capture timestamp with zone, par amount, bid/offer versus execution, currency and yield convention. An executed loan can still have undrawn commitments. Track eligibility and first draw separately.
4. **Apply to equity models.** Map eligible assets and available draws to spending by quarter. Assign corporate borrowings and residual equity to the uncovered need. Shock spread, draw delay, reserve and replacement capex separately. Track interest, principal, cash belonging to the project and the resulting diluted shares. Enter later transactions in a new dated edition.

## How to update

For each new filing or market observation, add the primary link and effective date to the issuer note, duplicate the current assumptions into a dated scenario and rerun the related script. Record the previous call, changed inputs, new result, unresolved assumptions and publication date in the tracker. Keep the November 25 price reference and November 27, 09:00 UTC information cutoff on the two original calls. November 27 US-session credit trades belong to the later credit review.
