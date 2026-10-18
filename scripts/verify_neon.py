"""Verify the existing Postgres URL without migrations or application writes.

Run after installing project dependencies. DATABASE_URL stays in the process
environment; neither exception messages nor credentials are printed.
"""
import json
import os
import re
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import psycopg


def verify(uri):
    report = {"authenticated_query": False, "tls": False, "write_read": False}
    try:
        parsed = urlsplit(uri or "")
        query = parse_qs(parsed.query, keep_blank_values=True)
        host = parsed.hostname or ""
        if (parsed.scheme not in ("postgres", "postgresql")
                or not re.fullmatch(r"[a-zA-Z0-9.-]+", host)
                or not parsed.username or not parsed.password
                or not parsed.path.strip("/")
                or query.get("sslmode", [""])[0] not in ("require", "verify-ca", "verify-full")):
            raise ValueError()
        parsed.port  # Validate before making a connection.
        report["host"] = host
        # Reject alternate destinations hidden in query parameters. A Neon URL
        # should have one endpoint, as copied from the console's Connect dialog.
        if (any(len(values) != 1 for values in query.values())
                or {"host", "hostaddr", "port", "dbname", "user", "password", "service"} & query.keys()):
            raise ValueError()
        psycopg.conninfo.conninfo_to_dict(uri)
    except (ValueError, TypeError, psycopg.Error):
        report["category"] = "invalid_configuration"
        return report

    try:
        with psycopg.connect(uri, connect_timeout=8, autocommit=True,
                             options="-c statement_timeout=5000 -c lock_timeout=2000") as conn:
            report["tls"] = bool(conn.pgconn.ssl_in_use)
            report["authenticated_query"] = conn.execute("SELECT 1").fetchone() == (1,)
            token = str(uuid4())
            # Session-local table: no application schema, records, or leases.
            # Commit drops it; disconnect also cleans it up after any failure.
            with conn.transaction():
                conn.execute("CREATE TEMP TABLE neocloud_connection_probe "
                             "(value text NOT NULL) ON COMMIT DROP")
                conn.execute("INSERT INTO neocloud_connection_probe VALUES (%s)", (token,))
                matched = conn.execute("SELECT value FROM neocloud_connection_probe").fetchone() == (token,)
            report["write_read"] = matched
        report["category"] = ("success" if all(report[k] for k in
                              ("authenticated_query", "tls", "write_read")) else "verification_failed")
    except Exception as exc:
        # libpq messages may contain a URI/password or provider details. Output
        # only fixed categories and SQLSTATE, never str(exc) or a traceback.
        state = getattr(exc, "sqlstate", None)
        if state and re.fullmatch(r"[A-Z0-9]{5}", state):
            report["sqlstate"] = state
        message = str(exc).lower()
        if state in ("28P01", "28000"):
            category = "authentication_failure"
        elif state == "42501":
            category = "insufficient_database_privileges"
        elif any(word in message for word in ("resolve", "name resolution", "translate host")):
            category = "dns_resolution_failure"
        elif "certificate" in message or "ssl handshake" in message:
            category = "tls_failure"
        elif isinstance(exc, psycopg.OperationalError):
            category = "connection_failure"
        else:
            category = "database_verification_failure"
        report["category"] = category
    return report


if __name__ == "__main__":
    result = verify(os.getenv("DATABASE_URL"))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["category"] == "success" else 1)
