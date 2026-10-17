import time
from fastapi.testclient import TestClient
from neocloud.app import app

def test_app_runs_without_database_or_inference_and_survives_browser_refresh(monkeypatch):
    monkeypatch.delenv("DATABASE_URL",raising=False)
    monkeypatch.delenv("CRUSOE_API_KEY",raising=False)
    with TestClient(app) as client:
        health=client.get("/api/health").json()
        assert "memory" in health["storage"]
        assert not health["database"]["connected"]
        assert not health["inference"]["verified"]
        assert client.get("/").status_code==200
        assert client.post("/api/runs",json={"tickers":["CRWV","NBIS"]}).status_code==503
        assert client.post("/api/runs",json={"tickers":["UNKNOWN"],"mode":"simulated"}).status_code==422
        response=client.post("/api/runs",json={"tickers":["CRWV","NBIS"],"mode":"simulated"})
        assert response.status_code==202
        run_id=response.json()["id"]
        for _ in range(60):
            run=client.get("/api/runs/"+run_id).json()
            if run["status"]=="completed":
                break
            time.sleep(.2)
        assert run["status"]=="completed"
        assert run["mode"]=="simulated"
        assert run["instruments"]
        assert "source_cache" not in run
        assert any(e["kind"]=="recursive_child" for e in run["events"])
        # New page requests read the same server-owned investigation.
        assert client.get("/?run="+run_id).status_code==200
        assert client.get("/api/runs/"+run_id).json()["tasks"]==run["tasks"]
        scenario=client.get("/api/runs/"+run_id+"/scenario?delta_bps=200").json()
        assert scenario["CRWV"]["known_annual_increment_by_currency"]=={}
        assert client.get("/api/runs/"+run_id+"/scenario?delta_bps=999").status_code==422

def test_source_retrieval_rejects_private_or_unapproved_destinations():
    import asyncio
    import pytest
    from neocloud.sources import retrieve
    for url in ("http://www.sec.gov/example","https://127.0.0.1/","https://www.sec.gov.evil.test/","https://user:pass@www.sec.gov/"):
        with pytest.raises(ValueError):
            asyncio.run(retrieve(url))
