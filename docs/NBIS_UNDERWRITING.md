# NBIS: funding before the share target

Information cutoff: **November 27, 2026 at 09:00 UTC**. Target date: **November 27, 2027**. Reference: **$84.99**, November 25 regular-session close, 16:00 US Eastern. The November 26 US holiday explains the dated observation; the after-hours quote is excluded. Research retrieval occurred after the cutoff but uses only earlier public disclosures.

Justin’s call is **Hold / high risk**. The conditional base value is **$95.50**, only **12.4%** above the reference, while total modeled existing-holder dilution reaches **34.7%**. This fails the stated 25% upside and maximum 25% dilution hurdles. The revenue outlook can be right while financing absorbs much of common-share upside.

| Case | Net equity cash gap | Financing shares | Target shares incl. awards | Total dilution | Conditional value | Return |
|---|---:|---:|---:|---:|---:|---:|
| Bear | $16.573B | 268.039M | 600.237M | 47.7% | $0.00 | -100.0% |
| Base | $11.361B | 151.557M | 480.754M | 34.7% | $95.50 | +12.4% |
| Bull | $6.959B | 87.504M | 441.895M | 28.9% | $267.72 | +215.0% |

These are financing scenarios, not consensus targets or a claim that a lender has agreed to provide the modeled project debt. The bear’s zero is an equity residual floor, not a prediction of a certain bankruptcy or a negative share price. Both enterprise-value assumptions and cash timing are contestable.

## What changed from the historical report

The original FY2027 base case reproduces exactly: **$12.55B revenue** and **−$24.7032B free cash flow**. It remains preserved in `original_reconstruction` with the complete original inputs, formula steps and source-file hash. Its $18.5B new customer advances were already added once, offset by $6.5B prepaid-revenue recognition. There is no demonstrated double count in that original FCF formula; treating the same advances as extra financing on top would create one.

The new bridge runs from September 30 to the actual target date, including the remaining 2026 spending period, known October investing cash use, conditional financing fees, Citi repayment, cash interest, a minimum reserve, equity issuance and award shares. Its cumulative target-date equity gap is not the same metric or horizon as annual FY2027 FCF. The operating anchor remains full FY2027 revenue and does not import December cash into the November valuation bridge.

## Reported cash, advances and financing

Reported September cash is $7.4256B **excluding** restricted cash of $1.2155B. The new calculator therefore uses `cash_includes_restricted: false`; subtracting the restricted amount again would be an error. The separate $1B minimum cash reserve is an assumption, not a legal restriction.

The nine-month $4.2311B operating cash flow already includes a $7.829B deferred-revenue movement. The deferred balance rises $7.8317B, a $2.7M difference not separately reconciled here. Neither figure establishes gross customer cash receipts. The $217.5M recognition disclosure covers only opening deferred revenue, so subtracting the net balance change from the $10B committed-advance guidance would invent a remaining cash receipt. Historical deferred revenue is never added again to opening cash.

Known October 1 construction-VIE lending of $230.6M is an investing use, not debt repayment. Further possible VIE funding is discretionary; Inferize consideration is not sufficiently disclosed to quantify. The known-transactions-only roll is not a certified current cash balance.

The October 22 $3.5B Citi agreement is a signed facility with unverified actual draw and fees. It is excluded from actual cash and separately assumed in each cash scenario, with a 1.5% fee and full repayment by the 364-day maturity on October 21, 2027. Additional project debt and its 2% modeled fee are transparent assumptions. The base’s $18.5B FY2027 advances plus $15.5B project loans represent 80% of annual $42.5B capex; this does not eliminate other operating, refinancing and reserve needs.

`upfront_financing_audit` separately reconciles older gross proceeds, discounts, fees, cash repayments and noncash exchanges. These pre-September proceeds are already in opening balances and never added twice. The August $800M note exchange for 15.770124M shares was noncash, not a cash debt repayment.

## Debt and the denominator

Debt uses the Note 12 $16.478B contractual principal/redemption claim, including future accretion conservatively upfront. This differs from both $14.1628B note carrying debt and $14.1908B balance-sheet carrying debt. The unresolved $28M discrepancy remains a conservative other-claim reserve; book minority equity contributes another $1M. No clean current EV or fabricated reconciliation is claimed.

Each of eight convertible tranches has its own original-principal coupon base and contractual underlying share formula. Coupons are **not** charged on the larger accreted redemption face. The base and bear retain all convertibles as debt. The bull assumes the June and September 2025 notes satisfy their trading-path conditions and convert on October 1, 2027: $3.8512B of claims removed, 26.194122M contractual shares added, and only subsequent coupons saved. The default bull value is $267.72; retaining every note instead gives $275.24. If the March 2026 tranches also become eligible, removing $9.0562B of total claims and adding 50.021939M total shares gives $265.29. Eligibility and holder election remain conditions; a target price alone does not establish an earlier sustained trading path.

Opening economic shares are 292.902405M ordinary shares plus 21.065936M nominal-strike prefunded warrants. Treasury shares and already completed ATM/exchange issuance are not added again. Note 13 provides 6.735333M parent options and 5.493478M parent RSUs at September 30; the older 9.736161M weighted EPS increment is not a point-in-time award count. The base conservatively reserves all 12.228811M outstanding awards plus 3M future awards and credits no option exercise cash. This is a modeled reserve, not a reported current fully diluted count. Subsidiary Avride awards are separate.

## Reverse test and the strongest objection

Holding target cash, debt, other claims, target shares and the base cash bridge fixed, **$84.99 requires 5.59753× FY2027 revenue**. This is a conditional reverse multiple, not an observed comparable valuation. The 4×/6×/8× multiple and 80%/100%/120% capex matrix reruns funding and dilution. At the unchanged 6× multiple, 20% lower spending raises modeled value to $132.32 and cuts the cash gap to $1.332B. Keeping revenue and financing unchanged despite lower investment is the optimistic assumption.

Management’s stronger customer prepayment terms and 75–85% projected capex coverage are the strongest objection to the cautious call. A Buy requires a refreshed bridge meeting the upside/dilution hurdles, documented receipt and draw timing funding at least 75% of planned capex, and delivery of remaining New Jersey capacity by Q2 2027. A funding shortfall without replacement or another delay impairing customer economics would weaken the rating.

## Evidence and practical limits

Primary sources, dates, periods, units and section/page locators are in `sources`; model operating assumptions are in each case’s `operating_assumptions`. The linked immutable baseline identifies inherited assumptions; new timing, loan access, issuance and valuation assumptions are authored in this review record and are not presented as issuer facts.

The November 12 detailed 6-K accession index was verified, accepted at 16:10:13 Eastern. Reviewed SEC daily indexes for November 17–25 show only NBIS Forms 4; the issuer newsroom’s latest reviewed financial release remains November 12. Full current SEC index extraction and exact post-September shares/draws are incomplete. No post-cutoff fact is used.

Quarterly operations/capex weights of 20/25/30/25 and earlier receipt weights of 30/30/25/15 are assumptions. Partial Q4 stops at November 27. Average-debt interest and period-end funding can understate intraperiod liquidity stress. No speculative strategic-investment sale or valuation plugs the gap. Cohort commissioning, capex classification, GPU economics, new borrowing terms, convert eligibility and customer-advance amortization remain material research gaps.

Validation: shared `build_underwriting` accepts the record, reproduces every displayed case value/return, and confirms that no embedded prepayment is added to cash a second time. Full repository regression and preview checks belong to the parent integration task.


## Valuation hurdle, nonoperating stakes and issuance capacity

The base 6× sales assumption is not an independently observed peer multiple. At modeled EBITDA margin 60.3%, it implies about 9.956× EBITDA; at 40% it implies 15× and at 30% it implies 20×. With illustrative maintenance capex of 25% of sales and cash tax of 2%, 5% and 7%, mature EBITDA margins of 30%, 40% and 60% yield only 0.5%, 1.7% and 4.7% unlevered cash yields on a 6× sales EV. These maintenance/tax inputs are assumptions, not issuer forecasts. The multiple needs continued growth; it does not make near-term cash consumption disappear.

Note 5 reports $1.5177B of ClickHouse, $83.7M of Toloka preferred and $2.5M of other nonmarketable stakes, totaling $1.6039B. They are not cash available for construction. The default assigns no separate credit because a current liquid mark, net sale proceeds and timing are unverified, not because the stakes have no value. Fully crediting reported carrying value without changing financing adds $3.34 per base share to $98.83 (+16.3%). This illustrative point is not a market-value upper bound. Consolidated Avride/TripleTen operating economics are not added again as standalone assets.

Only 7.636707M shares remained under the original ATM at September 30, versus 151.556791M hypothetical base financing shares. At the base gross issue price of $76.491, that dated capacity would yield about $584.14M gross or $572.46M after assumed 2% fees, far below the $11.36B gap. Current unused capacity is unverified. New issuance capacity, corporate approvals, sufficient unreserved share headroom and investors willing to buy at the assumed discount are conditions, not evidence already secured. The hypothetical equity calculation quantifies how large the problem is; it does not certify that the raise can close.
