# November 27 funding and common-equity review

The cutoff for issuer information is November 27, 2026 at 09:00 UTC. The price references are the November 25 US regular-session closes. The valuation horizon ends November 27, 2027. Cash needs accumulate from the September 30 opening balance through that target. Full FY2027 scenarios extend beyond the target.

| Company | Reference close | Net equity needed after modeled debt | All modeled existing-holder dilution | Base value | Return |
|---|---:|---:|---:|---:|---:|
| Nebius | $84.99 | $11.36B | 34.7% | $95.50 | +12.4% |
| CoreWeave | $42.57 | $7.74B | 28.5% | $48.60 | +14.2% |

The November 26 ledgers, three tactical calls and prior immutable editions remain available. This review is stacked on open PR #27 at `12e9c1e`. Default-branch head at the start was `48bef1e`. The existing research suite passed all 68 baseline checks. No production release notice is part of this edition.

- [Nebius assumptions, sources and unresolved claims](NBIS_UNDERWRITING.md)
- [CoreWeave assumptions, sources and unresolved claims](CRWV_UNDERWRITING.md)
- [Evidence check for every prior call and the next three research priorities](CALL_AUDIT_2026_11_27.md)
- [API resources and export policy](EQUITY_API.md)

## Reproduce and continue

1. From the review checkout, install the repository test dependencies with `python -m pip install -e '.[test]'`. Build the standard static app with `PYTHONPATH=. python scripts/build_neocloud_watch.py`.
2. Serve `work/neocloud-watch-site` with a static HTTP server. Open `/research/`, `/research/nbis/` and `/research/crwv/`. The standalone file `work/NCW-Equity-Research.html` includes all nine reports. The deployment setup is separate.
3. Inspect `neocloud/data/underwriting/{nbis,crwv}.json` for assumptions, transaction status and dated filing sections. Run `python -c "from neocloud.underwriting import load_underwriting; print(load_underwriting('NBIS')['computed']['cases'][1])"` to reproduce the base cash bridge, then substitute CRWV. New disclosures need an explicit cutoff, issuer-specific treatment and a fresh source check before changing assumptions.
4. Run `python -m pytest -q` and `npm ci && npm run test:watch`. With reviewed inputs finalized, `python scripts/equity_history.py` appends the new preview version and scorecard. Verify the nine reports, original calls, new inputs and current preview hashes before seeking release approval.

For the next research run, start with APLD project-to-parent cash flows, AGPU's single-date economic shares and accepted Georgia cash margin, then SHAZ's committed capex versus cash receipts and actual draws. Each has a dated source and a specific decision question in the call audit.

The standalone review runs on a separate Git branch. [Open the comparison](https://htmlpreview.github.io/?https://raw.githubusercontent.com/joedatacap/aidatacenter2/preview-funding-20261127/index.html), [Nebius](https://htmlpreview.github.io/?https://raw.githubusercontent.com/joedatacap/aidatacenter2/preview-funding-20261127/NBIS.html) or [CoreWeave](https://htmlpreview.github.io/?https://raw.githubusercontent.com/joedatacap/aidatacenter2/preview-funding-20261127/CRWV.html).
