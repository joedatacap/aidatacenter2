# CoreWeave financing and replacement test

**Decision: retain Hold at the November 25, 2026 close of $42.57.** Moving all $9 billion of modeled customer receipts back one quarter brings $6.00 billion of equity raising forward into Q4. Collection by Q2 restores the original financing total under the model’s constant issuance price. Mature-fleet cash conversion has the larger effect on per-share value. The base remains conditional on executing both debt draws and substantial new equity issuance.

**Dates.** The November 27, 2026 09:00 UTC information cutoff and November 27, 2027 valuation date from the original report are preserved. The separate credit research uses later US Friday trade observations. It contributes no retrospective cash inflows or changes to the dated equity case.

| Customer receipt assumption | Mature EBITDA converted to post-replacement, post-tax unlevered cash | Q4 2026 net equity | Total net equity through target | Financing shares | Existing-holder dilution | Value/share | Return from $42.57 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base timing | 60% | $1.16B | $7.74B | 206.19M | 28.46% | $48.60 | +14.17% |
| One quarter late | 60% | $7.16B | $7.74B | 206.19M | 28.46% | $48.60 | +14.17% |
| One quarter late, heavier replacement | 50% | $7.16B | $7.74B | 206.19M | 28.46% | $28.48 | −33.10% |
| One quarter late, lighter replacement | 65% | $7.16B | $7.74B | 206.19M | 28.46% | $58.66 | +37.80% |
| $9B absent through target | 60% | $7.16B | $16.74B | 445.89M | 45.32% | $37.15 | −12.74% |
| $9B absent through target, heavier replacement | 50% | $7.16B | $16.74B | 445.89M | 45.32% | $21.77 | −48.86% |

**Method.** The base collects $6B/$3B/$0 in Q4 2026/Q1 2027/Q2 2027. The delayed path collects $0/$6B/$3B. Each dollar changes operating cash once. Each path preserves the $3B cash reserve and reprices the residual equity at the model’s unchanged $42.57 reference less 10% discount and 2% fees. A forced raise at a deeper discount or failure to raise would worsen outcomes. The delayed path needs roughly 191M financing shares in Q4 alone, versus 35M available under the September 30 at-the-market program. Actual post-September capacity is unknown. The missed-receipts case holds operating delivery and contract recognition fixed to isolate the funding shock. A cancelled contract would also impair operating value. Quarter-end modeling cannot detect a within-quarter payment default. [10-Q, Notes 2, 10 and 11](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000465/crwv-20260930.htm) · [Management’s deposit outlook](https://s205.q4cdn.com/133937190/files/content_files/CoreWeave-3Q26-Transcript-_1_.pdf)

**Fleet economics.** The valuation capitalizes mature recurring unlevered cash at 11% required return and 2% growth using modeled $13.8B annual EBITDA. At 60% conversion, that is $8.28B after replacement spending and cash tax. At 50% it is $6.90B, equivalent to $1.38B/year additional replacement spending holding tax and other assumptions fixed. At 65% it is $8.97B. This stress changes the terminal economics. Actual 2027 bridge capex stays at the base path to avoid charging the same replacement spending twice. The original model supplies no separate verified mature-fleet replacement budget or cohort renewal yield.

**Decision triggers.** On the original financing path, the observed close needs 57.0% mature conversion and the 30% Buy hurdle needs 63.35%. If the $9B never arrives by target, the requirements rise to 63.53% and 71.83%. A favorable 65% case crosses the price hurdle only with receipts and executable financing. Monitor actual receipts or changes in refundability, closed eligible equipment funding, renewal cash margins and fleet refresh costs. Revisit the rating once evidence supports a different base. A persistent funding shortfall or corroborated decline toward 50% conversion would warrant a downgrade review.

**Reproduce.** Run `PYTHONPATH=. python scripts/crwv_scenarios.py` against PR #29’s November 27 underwriting inputs (commit `9dbc2d2`). The script calls the repository’s dated cash and valuation engine for each scenario and checks both receipt totals and base value. All numbers above are analyst scenarios.
