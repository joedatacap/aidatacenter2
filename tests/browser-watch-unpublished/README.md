# Unpublished custom-market interface tests

`markets.spec.cjs` preserves the November 22 custom price-return chart regression suite. Its clearly marked synthetic market inputs exist only in localhost test responses. They are not market research, public assets, or production source data.

The public interface now uses official external market widgets. This folder is outside `playwright.watch.config.cjs`'s production `testDir`; the custom-chart assertions must not claim coverage of that widget or extract its values. Production host/fallback, research navigation and export checks remain in `tests/browser-watch/`.

These cases can be adapted if a separately entitled custom-market interface returns. They require the old ranked/scatter/normalized chart implementation and `#market-data` contract, preserved in Git history with the November 22 feature. They are not runnable against the widget interface merely by changing the test directory. The independent market-validation Python tests continue to cover the parked ingestion/calculation model.
