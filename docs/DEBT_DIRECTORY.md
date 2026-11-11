# Actual borrowing comparison: methodology and evidence

Reviewed November 11, 2026. This is a curated snapshot, not a live market-data or
credit-rating service. The default screen covers the AI-infrastructure subset;
other peer-group filters add context without calling every company a neocloud.

## What the user can compare

1. **Reported borrowings, excluding leases.** USD consolidated carrying amounts of
   loans and notes, net of disclosed discounts and issue costs. This measures
   borrowing size, not all liabilities, face principal, available credit or
   repayment ability. Both operating and finance lease liabilities are excluded;
   those are real economic obligations, especially for lease-heavy operators.
2. **Borrowings / total assets.** Same-date borrowings divided by consolidated
   recorded assets, expressed as dollars of borrowing per $100 of assets. It
   does not identify which assets were funded by debt. Construction assets,
   crypto holdings, fair values and lease right-of-use assets make business-model
   comparisons imperfect. This is not debt/equity, debt/EBITDA or a health score.
3. **Bond coupon examples.** A sortable, unnumbered reference to one identified USD
   fixed-rate instrument per company where independently reviewed. The selection
   is a documented example, not a claim to the lowest, latest or average funding
   cost. Convertibles/exchangeables have equity-option economics; project notes
   and unsecured corporate notes have different security and recourse. Coupon
   differs from current market yield. Continued outstanding status is not
   reverified for every historical example.

There are two company rankings and one instrument reference, rather than three
misleading company-health rankings. No market-cap denominator or current bond
quotes are invented. Numerical ordering describes only the selected accounting
metric within the chosen filter, not creditworthiness.

## Coverage and dates

| Business group | Companies | Balance-sheet dates |
|---|---|---|
| GPU cloud | CRWV, NBIS | September 30; NBIS June 30 |
| AI infrastructure / mixed transition | IREN, BTDR, HUT, APLD, CORZ, WULF, CIFR, HIVE, GLXY | September 30; APLD August 31 |
| Bitcoin mining / adjacent | RIOT, MARA | September 30 |
| Data-center REITs | EQIX, DLR | September 30 |

All dates are in 2026. These are not exhaustive sector classifications or a claim
that AI is each company's principal business. Private operators without comparable
public financial statements are not filled with estimates just to increase breadth.

Fourteen companies have reconciled borrowing totals and same-date asset ratios.
Galaxy's dollar loans and notes are an incomplete subset of its financing
obligations; digital-asset borrowing/collateral liabilities need further work.
Its borrowing total and asset ratio therefore stay null and unranked. Its cash,
assets and one named project-note coupon remain separately sourced.

## Important scope cases

- CoreWeave's latest reviewed quarter-end release is November 10. Recourse and
  nonrecourse current/noncurrent borrowing rows sum to the numerator; leases stay
  separate. Nonrecourse does not mean a blanket claim on the parent.
- Nebius retains June 30 debt/assets. The subsequent August convertible issue is
  a separate coupon observation, not a pro-forma update to the earlier balance
  sheet. Its next reported results were scheduled November 12 at the review cutoff.
- Hut 8 uses $7.628225B borrowing carrying amount, excluding a $3.275M SAFE from
  a combined balance-sheet liability caption and separately classified miner
  purchase obligations. Restricted project cash is not unrestricted parent cash.
- Cipher's full borrowing reconciliation includes vehicle loans omitted from a
  smaller fair-value table. The full debt note and current/noncurrent rows agree.
- MARA's later $750M loan repayment is noted without changing September 30 assets
  or borrowings. Crypto assets and receivables are not counted as cash.
- Equinix source tables are rounded to USD millions. Dollar conversion does not
  create additional precision. Digital Realty's own net-debt/EBITDA measure uses
  JV and lease adjustments and is not substituted for this common asset ratio.
- Galaxy's cash is the balance-sheet cash/equivalents line, not its broader
  cash/stablecoin/Treasury liquidity headline. Qualifying short-term Treasuries
  may already be within cash equivalents; separately classified investments stay
  outside that line.

## Evidence and calculation boundary

`neocloud/data/debt_directory.json` is the curated source of truth. It contains
dated amounts, component reconciliations, explicit definitions, short exact
source passages and primary URLs. No credentials or live research-run snapshots
are exported. Source publication dates are separate from bond issue dates and
financial statement dates.

`neocloud/directory.py` validates sources, rejects synthetic inputs, checks
component sums and same-date/consolidated/currency scope, and computes ratios
with Decimal. `scripts/build_debt_preview.py` produces `preview/data.json`.
JavaScript sorts and formats these exported values; it does not implement a
second financial model. Missing values never become zero. A genuine zero coupon
remains 0%, rather than being treated as unavailable.

The older synthetic scenario engine and fixtures are preserved separately at
`preview/scenarios/`; they cannot enter the source-backed directory.

## Delivery and operational limits

The static preview needs no API, database or inference key. HTML, CSS, JS and
curated read-only data can be hosted using the prepared Cloudflare Free Static
Assets configs, including a tested `/neoclouddebt/` prefix. No public deployment,
merge, paid feature or research-runtime migration is part of this change.

The standalone HTML embeds the whole directory and works without a server or
network. Source links need internet access when opened. Tests verify rankings,
unknown handling, grouping, coupon separation, exports, URL restoration,
keyboard interaction, source details, mobile layout and offline operation.
