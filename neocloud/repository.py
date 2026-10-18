"""Neon production store, explicit nonpersistent in-memory development adapter."""
import asyncio
import copy
import os
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from .catalog import COMPANIES


class MemoryRepository:
    mode = "memory (development only; lost on server restart)"
    def __init__(self):
        self.runs = {}
    async def initialize(self):
        return None
    async def save(self, run):
        self.runs[run["id"]] = copy.deepcopy(run)
    async def get(self, run_id):
        return copy.deepcopy(self.runs.get(run_id))
    async def all(self):
        return copy.deepcopy(list(self.runs.values()))
    async def heartbeat(self):
        return None
    async def close(self):
        return None


class PostgresRepository:
    mode = "Neon/Postgres"
    def __init__(self, url):
        parsed = urlsplit(url)
        if not parsed.hostname:
            raise ValueError('DATABASE_URL must include a hostname')
        parsed.port  # Validate the port before any connection attempt.
        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError("DATABASE_URL must be a Postgres URI")
        if parse_qs(parsed.query).get("sslmode", [""])[0] not in ("require", "verify-ca", "verify-full"):
            raise ValueError("DATABASE_URL must require TLS with sslmode=require or stronger")
        self.url = url
        self.owner = str(uuid4())
        self.leased = False

    def _connection(self):
        return psycopg.connect(self.url,connect_timeout=10)

    async def initialize(self):
        await asyncio.to_thread(self._initialize)

    def _initialize(self):
        with self._connection() as conn:
            conn.execute(Path(__file__).with_name("schema.sql").read_text())
            for ticker, company in COMPANIES.items():
                conn.execute("INSERT INTO companies VALUES (%s,%s,%s,%s,%s) ON CONFLICT(ticker) DO NOTHING",
                             (ticker, company["name"], company["base_currency"], company["sector"], company["url"]))
        # Row lease works through Neon's transaction pooler; no session locks required.
        self._heartbeat()

    def _heartbeat(self):
        with self._connection() as conn:
            row = conn.execute("""INSERT INTO worker_leases(name,owner,expires_at)
                VALUES('research',%s,now()+interval '120 seconds')
                ON CONFLICT(name) DO UPDATE SET owner=EXCLUDED.owner,expires_at=EXCLUDED.expires_at
                WHERE worker_leases.owner=EXCLUDED.owner OR worker_leases.expires_at < now()
                RETURNING owner""",(self.owner,)).fetchone()
            if row is None:
                raise RuntimeError("Another worker owns this database queue")
            self.leased=True

    async def heartbeat(self):
        await asyncio.to_thread(self._heartbeat)

    async def save(self, run):
        await asyncio.to_thread(self._save, copy.deepcopy(run))

    def _save(self, run):
        # Refuse writes after ownership is lost.
        self._heartbeat()
        with self._connection() as conn:
            conn.execute("""INSERT INTO runs(id,status,created_at,body) VALUES(%s,%s,%s,%s)
                ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,body=EXCLUDED.body,updated_at=now()""",
                (run["id"], run["status"], run["created_at"], Jsonb(run)))
            for task in run["tasks"]:
                conn.execute("""INSERT INTO tasks(id,run_id,parent_task_id,ticker,role,status,retries,body)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                    status=EXCLUDED.status,retries=EXCLUDED.retries,body=EXCLUDED.body""",
                    (task["id"],run["id"],task["parent_task_id"],task.get("ticker"),task["role"],
                     task["status"],task["retries"],Jsonb(task)))
            for event in run["events"]:
                conn.execute("INSERT INTO agent_events VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                             (event["id"],run["id"],event.get("task_id"),event["timestamp"],Jsonb(event)))
            for evidence in run["evidence"]:
                conn.execute("INSERT INTO evidence VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                    (evidence["id"],run["id"],evidence["source_url"],evidence["retrieved_at"],Jsonb(evidence)))
            for item in run["instruments"]:
                conn.execute("""INSERT INTO instruments VALUES(%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(run_id,instrument_id) DO UPDATE SET body=EXCLUDED.body,
                    outstanding_principal=EXCLUDED.outstanding_principal,
                    currency=EXCLUDED.currency,snapshot_date=EXCLUDED.snapshot_date""",
                    (run["id"],item["instrument_id"],item["ticker"],item.get("outstanding_principal"),
                     item["currency"],item.get("snapshot_date"),Jsonb(item)))
            for item in run["customer_deals"]:
                conn.execute("INSERT INTO customer_deals VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                             (item["id"],run["id"],item["ticker"],Jsonb(item)))
            for item in run.get("deal_financing_links",[]):
                conn.execute("INSERT INTO deal_financing_links VALUES(%s,%s,%s) ON CONFLICT(id) DO UPDATE SET body=EXCLUDED.body",
                             (item["id"],run["id"],Jsonb(item)))
            for item in run["market_observations"]:
                conn.execute("INSERT INTO market_observations VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                             (item["id"],run["id"],item["ticker_or_security"],item["observation_date"],
                              item["metric_type"],item["value"],Jsonb(item)))

    async def get(self, run_id):
        return await asyncio.to_thread(self._get, run_id)
    def _get(self, run_id):
        with self._connection() as conn:
            row = conn.execute("SELECT body FROM runs WHERE id=%s", (run_id,)).fetchone()
            return row[0] if row else None
    async def all(self):
        return await asyncio.to_thread(self._all)
    def _all(self):
        with self._connection() as conn:
            return [row[0] for row in conn.execute("SELECT body FROM runs ORDER BY created_at DESC LIMIT 100")]
    async def close(self):
        if self.leased:
            await asyncio.to_thread(self._release)
            self.leased=False

    def _release(self):
        with self._connection() as conn:
            conn.execute("DELETE FROM worker_leases WHERE name='research' AND owner=%s",(self.owner,))


def make_repository():
    url = os.getenv("DATABASE_URL")
    if not url:
        return MemoryRepository()
    transport=os.getenv('DATABASE_TRANSPORT','auto')
    if transport=='postgres':
        return PostgresRepository(url)
    from .neon_http import NeonHTTPRepository,AutoNeonRepository
    if transport=='neon_http':
        return NeonHTTPRepository(url)
    if transport!='auto':
        raise ValueError('DATABASE_TRANSPORT must be auto, postgres or neon_http')
    return AutoNeonRepository(url) if (urlsplit(url).hostname or '').endswith('.neon.tech') else PostgresRepository(url)
