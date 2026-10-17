"""Real TLS Postgres integration, optional outside CI. No SQLite substitution."""
import asyncio
import os
import pytest
import psycopg
from neocloud.engine import Engine, new_run, event
from neocloud.finance import Instrument
from neocloud.repository import PostgresRepository

@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"),reason="Dedicated TLS Postgres test database not configured")
def test_neon_repository_schema_atomic_snapshot_recovery_and_worker_ownership():
    async def check():
        uri=os.environ["TEST_DATABASE_URL"]
        first=PostgresRepository(uri)
        second=PostgresRepository(uri)
        await first.initialize()
        try:
            with pytest.raises(RuntimeError,match="Another worker"):
                await second.initialize()
            run=new_run(["IREN"],"simulated")
            run["status"]="running"
            run["tasks"][0]["status"]="running"
            run["budgets"]["llm_calls"]=1
            run["evidence"]=[{"id":run["id"]+"-e","source_url":"https://iren.com/test-fixture",
                               "retrieved_at":run["created_at"],"excerpt":"Integration test fixture","provenance":"fixture"}]
            run["instruments"]=[Instrument(instrument_id="IREN:test",ticker="IREN",name="TEST FIXTURE",
                currency="USD",outstanding_principal="123.45",snapshot_date="2026-06-30",
                rate_type="floating",evidence_ids=[run["evidence"][0]["id"]],provenance="fixture").model_dump(mode="json")]
            event(run,"test","Integration test event",run["tasks"][0]["id"])
            await first.save(run)
            await first.save(run)  # Idempotent task, event, evidence, instrument upserts.
            with psycopg.connect(uri) as conn:
                assert conn.execute("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()").fetchone()[0]
                assert conn.execute("SELECT count(*) FROM instruments WHERE run_id=%s",(run["id"],)).fetchone()[0]==1
                assert conn.execute("SELECT count(*) FROM agent_events WHERE run_id=%s",(run["id"],)).fetchone()[0]==1
            await first.close()
            await second.initialize()
            await Engine(second,None).recover()
            restored=await second.get(run["id"])
            assert restored["tasks"][0]["status"]=="pending"
            assert restored["tasks"][0]["retries"]==1
            assert restored["budgets"]["llm_calls"]==1
            assert restored["instruments"][0]["outstanding_principal"]=="123.45"
        finally:
            await first.close()
            await second.close()
    asyncio.run(check())
