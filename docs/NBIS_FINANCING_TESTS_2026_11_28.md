# Nebius financing review | November 28, 2026

**Keep Hold / high risk at the November 25 close of $84.99.** Even combining the low end of spending guidance with the high ends of revenue, customer advances and financing coverage produces 29.55% dilution. The report requires at least 25% upside and at most 25% dilution. Both are possible in this model, but the passing path requires earlier collections and a large equity placement above the historical closing price.

All cases use the November 27 information cutoff, a November 27, 2027 valuation date, the PR #29 base cost structure and 6× revenue. Values are conditional on completing the indicated financing. The dated report and decision rules are [in the underwriting](NBIS_UNDERWRITING.md). FY2027 revenue, spending and capex coverage ranges are from the [November 12 shareholder letter](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126008/tm2629571d1_ex99-2.htm).

| What changes from the dated base | Net equity needed | Financing shares | Total dilution | Value/share | Upside | Both numeric hurdles |
|---|---:|---:|---:|---:|---:|---|
| Dated base | $11.36B | 151.56M | 34.69% | $95.50 | 12.36% | Fail |
| Fund 85% of capex by borrowing more, other base assumptions held | $9.52B | 127.00M | 31.18% | $96.41 | 13.44% | Fail |
| All planned FY2027 customer advances arrive one quarter late | $14.82B | 197.70M | 40.41% | $87.13 | 2.52% | Fail |
| $40B capex, $20B advances, 85% coverage, $12B revenue | $9.28B | 123.73M | 30.68% | $97.08 | 14.23% | Fail |
| Same funding and spending with $13B revenue | $8.73B | 116.43M | 29.55% | $112.14 | 31.94% | Fail dilution |
| Same funding and spending, $12.55B revenue, Q4 receipts moved into Q1 | $7.87B | 104.93M | 27.68% | $108.89 | 28.12% | Fail dilution |
| Previous row with equity sold at $90 gross per share | $7.87B | 89.18M | 24.96% | $112.99 | 32.94% | Pass conditionally |

The last row moves $3B of planned Q4 advances into Q1 and assumes a future $100 issuance reference, a 10% placement discount and 2% issuance fees. All reported returns still use the original $84.99 close. At the assumed $90 gross price, investors must purchase about $8.03B of stock. The September 30 at-the-market program showed 7.64M remaining shares. Neither an offering on these terms nor accelerated customer payments were established at the cutoff. Even if financing improves, an upgrade also requires evidence of the promised New Jersey delivery by Q2 2027. [Filed statements, Notes 13–14](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126238/nbis-ex99d2.htm) · [Management's delivery timetable](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126008/tm2629571d1_ex99-2.htm)

**The dilution ceiling sets the financing budget.** Opening economic shares of 313.97M and the 15.23M modeled award reserve leave room for 89.43M financing shares at 25% total dilution. At the base net proceeds of $74.96 per share, the gap must fall to **$6.70B**. In the early-receipt case the gap is $7.87B, requiring at least $89.75 gross per share after allowing for the 2% fee. Prepayment and project debt have different effects on shareholder value. Borrowing more raises the senior claims deducted from enterprise value. Advancing cash receipts can reduce equity needs through the valuation date but also changes cash available afterward.

### Citi maturity and liquidity

The [October financing 6-K](https://www.sec.gov/Archives/edgar/data/1513845/000110465926117978/tm2628078d1_6k.htm) provides October 17, 2026 as the agreement date and October 16, 2027 as maturity. [Q3 subsequent events, F-41](https://www.sec.gov/Archives/edgar/data/1513845/000110465926126238/nbis-ex99d2.htm), instead describes an October 22 signing and a 364-day term. The 6-K was filed October 22. Use its explicit earlier maturity for liquidity planning. No actual draw amount or date is established by those disclosures.

Assuming the full $3.5B was drawn, scheduling its repayment on October 16 puts **$3.55B of modeled equity funding on that day** to preserve the $1B liquidity reserve. This requires all prior modeled equity to have been raised and assumes other cash flows arrive evenly within the quarter. Date-specific repayment produces a $11.35B cumulative gap, 34.68% dilution and $95.52/share (+12.39%). The period-averaged baseline gives $95.50. The early cash requirement matters far more than the two-cent valuation difference. The parent is a co-borrower and substantially all borrower assets secure the bridge, subject to exclusions. Its SOFR spread starts at 275bp and rises by 25bp per 90 days to 350bp. Its rate and security differ from a GPU project facility with an assigned offtake contract.

### Reproduction and assumptions

Run `PYTHONPATH=. python scripts/nbis_financing_review.py` at the repository root. The script calls `evaluate_case` from the same underwriting engine used by the reports, with the original 2026 periods, debt amortization, 6% aggregate nonconvertible-debt rate assumption, reserve and awards. The rate is a sensitivity input for multiple instruments. A forward Term SOFR path for the Citi loan has not been projected separately.

- FY2027 project debt equals spending times assumed coverage less full-year advances. It carries the original 2% issuance fee. In the $40B / $20B / 85% examples, this implies $14B of project debt versus $15.5B in the base.
- Spending and project loans use 20% / 25% / 30% / 25% quarter weights. Base client receipts use 30% / 30% / 25% / 15%. The delayed case leaves the prior quarter's 2026 receipts unchanged and moves each 2027 receipt one quarter later. The final year-quarter includes only 58 of 92 days. Receipts enter operating cash once. The existing prepaid-service recognition schedule stays fixed, so this is a collection timing test assuming no contract changes or financing penalties.
- For the $12B and $13B revenue sensitivities, change recurring operating cash by the change in revenue times the base 60.27% EBITDA margin, weighted by the quarterly operating schedule. These are approximations, not site-level forecasts. The upper case requires more revenue for less spending than the base. No new conversion, offering, lender draw, customer payment or physical capacity is treated as established.
- The maturity sensitivity retains the original assumption of a draw within the period starting October 22, then splits the last 58 days at October 16, 2027. It assigns the full modeled Citi principal repayment to that day and prorates other flows by elapsed days. The model assumes equity can be placed when needed. Actual financing must be arranged before the due date.
