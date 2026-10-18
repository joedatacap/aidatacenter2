# Neon connection investigation — October 17, 2026

Started from latest `main`, commit `482d0919dbaaa9977d62de7e994c49656bb47a6e`,
on separate branch `codex/fix-neon`. No application persistence implementation,
financial calculations, research agents, dashboard, or V2 schema was changed.

## Result

**Blocked by this managed runtime's network configuration. No authenticated Neon
query or Neon write/read succeeded.** Investigation stopped after one database
connection attempt and one HTTPS route probe; unchanged paths were not retried.

The configured URL has a PostgreSQL scheme, username/password/database fields,
port 5432, and `sslmode=require` or stronger. Its hostname is:

```text
ep-snowy-star-b5wdg6du-pooler.c-7.us-east-2.aws.neon.tech
```

This matches Neon's pooled hostname structure. It is not proof that the endpoint,
database name, or credentials are current. Compare them privately with the Neon
console's **Connect** dialog. A successful SQL Editor `SELECT 1` proves the console
can reach a database; it does not authenticate the application's configured URL.
No credential or database-name value was displayed or saved.

Observed in this runtime:

| Check | Result |
| --- | --- |
| Database hostname lookup | `gaierror`, temporary DNS resolution failure |
| Authenticated PostgreSQL attempt, 8-second connect timeout | Failed during DNS resolution; no session established |
| Startup network snapshot, version 1 | Restricted HTTP; empty TCP domains and IP ranges; VPN not configured |
| Current environment status | Running, but network policy and DATABASE_URL readiness states reported `unknown` |
| POST route probe to regional Neon `/sql`, without credentials | HTTP proxy `403 Forbidden`, before reaching Neon |

Codex Cloud's managed runtime has a TCP forwarding facility, but this instance has
no grants and no general direct Internet route. Its HTTP proxy is not a PostgreSQL
wire-protocol connection. Adding an HTTP hostname rule alone cannot enable raw
PostgreSQL on port 5432. This finding applies to this instance; it is not a claim
that every Codex environment lacks outbound database support. Do not infer an
invalid hostname, rejected password, or Neon outage from these network failures.

## Exact HTTPS permission

Neon's supported SQL-over-HTTPS endpoint for this connection is:

```text
https://api.c-7.us-east-2.aws.neon.tech/sql
```

Allow **general outbound HTTPS to `api.c-7.us-east-2.aws.neon.tech`, TCP 443** in
the managed environment's network configuration, including POST `/sql`. This is
separate from Crusoe's API-key allowed-domain binding. Apply the configuration to
the running/replacement environment and verify its effective policy. Keep the
existing `DATABASE_URL` as a secure process variable. SQL-over-HTTPS authenticates
using that URL in the `Neon-Connection-String` request header over verified TLS;
do not put it in a URL, command argument, log, or browser response. Redirects must
remain disabled for credential-bearing requests.

The endpoint rule is confirmed by Neon's official serverless driver 1.2.0
[source](https://github.com/neondatabase/serverless/blob/main/src/shims/net/index.ts):
replace the first database DNS label with `api.` and append `/sql`. Neon's
[transaction API](https://github.com/neondatabase/serverless#transaction) supports
non-interactive atomic query batches. Latest main already contains a Python
adapter for that protocol and the application's batched repository writes.
It remains unchanged and unverified against real Neon. No additional adapter,
provider, or transport rewrite is justified by a denied route probe.

## Simplest path to persistence

Run the existing app on a normal application runtime with DNS and outbound TLS
PostgreSQL access to the database hostname on port 5432. Use the same secret URL
and set `DATABASE_TRANSPORT=postgres` to select the existing PostgreSQL repository.
After installing the project dependencies, run:

```sh
python scripts/verify_neon.py
```

The verifier reads only `DATABASE_URL` from the process environment. It exits zero
only after an authenticated `SELECT 1`, confirmed TLS, and parameterized temporary
table write/read with a successful transaction commit. The temporary table is
dropped at commit/disconnect. The role needs database CONNECT and TEMP privileges.
It runs no migrations, touches no application records or worker leases, and emits
only a hostname, fixed categories, booleans, and optional SQLSTATE.

This checks SQL connectivity and session-local write/read, not committed
application persistence across new sessions or restart. After it succeeds, start
the app with one Uvicorn worker and verify an application save/read/restart using
its existing repository. Never point the destructive integration test suite's
`TEST_DATABASE_URL` at the user's Neon database.

Alternatively, enable the exact HTTPS rule above, perform a genuine authenticated
query through the existing adapter, then verify real save/read/recovery before
calling that transport production-ready. A successful policy change alone is not
a successful database test.

## Validation

- All **56 existing tests passed**, including both database integration tests,
  with `TEST_DATABASE_URL` targeting a newly created disposable PostgreSQL 16
  container with TLS enabled. This includes real repository save/read/recovery,
  worker ownership, and the HTTPS protocol bridge's atomic rollback test.
- The new verifier passed authenticated SQL, TLS, and temporary-table write/read
  against that disposable database. Failure-redaction and invalid-configuration
  checks also passed.
- The HTTPS bridge mocks the Neon HTTP boundary and executes real PostgreSQL SQL;
  it does not prove Neon HTTPS access. No actual Neon query/write/read succeeded.
- No application modules or schema files changed. Only the verifier and
  documentation are committed on `codex/fix-neon`; no application integration fix
  or PR is claimed because real Neon success was not achieved.
