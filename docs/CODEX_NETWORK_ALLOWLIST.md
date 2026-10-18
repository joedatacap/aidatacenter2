# Codex Cloud Network Allowlist — NeoCloud Debt Intelligence

**Date:** 2026-10-17. Proposed targets to add in **Settings → Codex Cloud → Environments → Edit → Internet access → Additional allowed domains**. This document does **not** change the actual Codex Cloud environment.

## Currently configured (per user's prior published-environment screenshot)

```text
api.inference.crusoecloud.com
www.sec.gov
investors.coreweave.com
nebius.com
iren.com
ir.bitdeer.com
```

Verify against actual environment; don't blindly duplicate existing entries.

## Add to support current V2 and upcoming integration

```text
api.c-7.us-east-2.aws.neon.tech
data.sec.gov
www.hut8.com
api.stlouisfed.org
ydc-index.io
api.you.com
api.github.com
raw.githubusercontent.com
```

- Neon regional SQL-over-HTTPS: `api.c-7.us-east-2.aws.neon.tech`, **POST /sql**, exact environment-specific host from `docs/NEON_CONNECTIVITY.md` on `codex/fix-neon`. This only permits HTTP traffic; actual authenticated SQL query/write/read remains unverified. Direct Postgres TCP 5432 requires separate forwarding grant and is not unlocked by domain HTTPS allowlist.
- SEC structured data JSON uses `data.sec.gov`; filings use existing `www.sec.gov`.
- Hut 8 issuer financing releases are on `www.hut8.com`.
- FRED time series uses `api.stlouisfed.org` and requires FRED API key (unless an authorized public download route is chosen).
- You.com Web Search and Contents APIs use `ydc-index.io`; its Answer, Research and Finance Research APIs use `api.you.com`. Optional paid/credited API; access does not grant credentials.
- GitHub REST and raw files use `api.github.com` and `raw.githubusercontent.com`; GitHub plugin/app access might already suffice.

## Optional for later work (add only if activating corresponding integration)

```text
api.cloudflare.com
developers.cloudflare.com
api.neon.tech
docs.cloud.crusoe.ai
www.newyorkfed.org
markets.newyorkfed.org
www.federalreserve.gov
www.reuters.com
stooq.com
```

- Cloudflare API for future deployment uses its own scoped token; documentation does not need credentials.
- Neon management API not needed for existing DATABASE_URL.
- NY Fed/Fed for reference rates; FRED may suffice.
- Reuters for context and Stooq for market observations only if licensing, availability and factual accuracy have been checked. These are not guaranteed institutional-grade bond yield sources.
- Do not enable arbitrary bond/stock data vendors without choosing an approved provider and verifying its permitted API endpoint and commercial terms.

## Setup rules

1. Use Codex environment **Package managers** preset for normal Python/Node install hostnames instead of manually adding dozens of registries; it includes `pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org`, common GitHub download hosts.
2. Enable methods needed by the APIs; **POST is necessary for Crusoe chat completions, Neon HTTPS SQL, You.com search and many managed APIs**. A GET-only network policy will not work for them.
3. `CRUSOE_API_KEY` remains a **Network secret restricted exclusively to `api.inference.crusoecloud.com`**. Do NOT attach it to all research hosts. `DATABASE_URL` remains a private environment variable; never paste real credentials into repo.
4. Allowlist is not authentication, and cannot guarantee HTTP 200. Corporate issuer hosts can still block automation; implement explicit source failure states. If app code has its own source-host whitelist, update it deliberately for new approved primary sources.
5. After editing, **Republish**, then **start a new cloud task** for the published policy. Existing cloud tasks retain their own workspace state.
6. Do not choose unlimited Internet access or permit broad wildcard hosts just to avoid occasional updates; restrict sensitive operations and validate remote content against prompt injection/exfiltration.
7. Record the exact host of any new service in this file and only add it to the cloud allowlist when it is required.

## Verified documentation

- https://learn.chatgpt.com/docs/environments/cloud-environments
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://you.com/docs/guides/search
- https://www.hut8.com/news-insights/press-releases
