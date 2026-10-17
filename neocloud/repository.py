"""Neon production store, explicit nonpersistent in-memory development adapter."""
import asyncio
import copy
import os
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
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
    async def close(self):
        return None


class PostgresRepository:
    mode = "Neon/Postgres"
    def __init__(self, url):
        parsed = urlsplit(url)
        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError("DATABASE_URL must be a Postgres URI")
        if parse_qs(parsed.query).get("sslmode", [""])[0] not in ("require", "verify-ca", "verify-full"):
            raise ValueError("DATABASE_URL must require TLS with sslmode=require or stronger")
        self.url = url
        self.lease = None

    async def initialize(self):
        await asyncio.to_thread(self._initialize)

    def _initialize(self):
        with psycopg.connect(self.url, connect_timeout=10) as conn:
            conn.execute(Path(__file__).with_name("schema.sql").read_text())
            for ticker, company in COMPANIES.items():
                conn.execute("INSERT INTO companies VALUES (%s,%s,%s,%s,%s) ON CONFLICT(ticker) DO NOTHING",
                             (ticker, company["name"], company["base_currency"], company["sector"], company["url"]))
        # One worker process owns the queue; fail visibly rather than run duplicate model calls.
        self.lease = psycopg.connect(self.url, connect_timeout=10, autocommit=True)
        if not self.lease.execute("SELECT pg_try_advisory_lock(734903211)").fetchone()[0]:
            self.lease.close()
            self.lease = None
            raise RuntimeError("Another worker owns this database queue; use one Uvicorn worker")

    async def save(self, run):
        await asyncio.to_thread(self._save, copy.deepcopy(run))

    def _save(self, run):
        # Check the worker's dedicated lock connection before each persistent transition.
        self.lease.execute("SELECT 1")
        with psycopg.connect(self.url, connect_timeout=10) as conn:
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

    async def get(self, run_id):
        return await asyncio.to_thread(self._get, run_id)
    def _get(self, run_id):
        with psycopg.connect(self.url, connect_timeout=10) as conn:
            row = conn.execute("SELECT body FROM runs WHERE id=%s", (run_id,)).fetchone()
            return row[0] if row else None
    async def all(self):
        return await asyncio.to_thread(self._all)
    def _all(self):
        with psycopg.connect(self.url, connect_timeout=10) as conn:
            return [row[0] for row in conn.execute("SELECT body FROM runs ORDER BY created_at DESC LIMIT 100")]
    async def close(self):
        if self.lease:
            await asyncio.to_thread(self.lease.close)


def make_repository():
    url = os.getenv("DATABASE_URL")
    return PostgresRepository(url) if url else MemoryRepository()
