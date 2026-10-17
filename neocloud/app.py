import asyncio
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from .catalog import COMPANIES
from .crusoe import Crusoe, InferenceError
from .engine import Engine, new_run
from .finance import Instrument, rate_scenario, refinancing_scenario
from .repository import make_repository, MemoryRepository

STATIC = Path(__file__).with_name("static")

@asynccontextmanager
async def lifespan(app):
    app.state.crusoe = Crusoe()
    app.state.inference = {"verified":False,"reason":"CRUSOE_API_KEY not configured"}
    if app.state.crusoe.key:
        try:
            app.state.inference = {"verified":True,**await app.state.crusoe.verify()}
        except (InferenceError,httpx.HTTPError):
            app.state.inference = {"verified":False,"reason":"Crusoe connectivity or structured-output verification failed"}
    app.state.database = {"configured":False,"connected":False}
    candidate_repo = None
    try:
        candidate_repo = make_repository()
        await candidate_repo.initialize()
        repo = candidate_repo
        app.state.database = {"configured":not isinstance(repo,MemoryRepository),
                              "connected":not isinstance(repo,MemoryRepository)}
    except Exception:
        if candidate_repo is not None:
            await candidate_repo.close()
        repo = MemoryRepository()
        app.state.database = {"configured":True,"connected":False,
                              "warning":"Postgres unavailable; using nonpersistent development memory"}
    app.state.repo = repo
    app.state.engine = Engine(repo,app.state.crusoe)
    worker = asyncio.create_task(app.state.engine.serve())
    app.state.worker = worker
    try:
        yield
    finally:
        app.state.engine.stop.set()
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
        await repo.close()

app = FastAPI(title="NeoCloud Debt Intelligence",lifespan=lifespan)
app.mount("/static",StaticFiles(directory=STATIC),name="static")

class RunRequest(BaseModel):
    tickers: list[str] = Field(min_length=1,max_length=2)
    mode: Literal["live","simulated"] = "live"

    @model_validator(mode="after")
    def supported(self):
        self.tickers = list(dict.fromkeys(t.upper().strip() for t in self.tickers))
        if any(t not in COMPANIES for t in self.tickers):
            raise ValueError("Supported tickers: CRWV, NBIS, IREN, BTDR")
        return self

@app.get("/")
async def home():
    return FileResponse(STATIC / "index.html")

@app.get("/api/health")
async def health():
    return {"storage":app.state.repo.mode,"database":app.state.database,
            "inference":app.state.inference,"worker":not app.state.worker.done()}

@app.get("/api/companies")
async def companies():
    return COMPANIES

@app.post("/api/inference/verify")
async def verify():
    try:
        result = await app.state.crusoe.verify()
        app.state.inference = {"verified":True,**result}
        return app.state.inference
    except (InferenceError,httpx.HTTPError):
        app.state.inference = {"verified":False,"reason":"Crusoe verification failed; check secure runtime configuration"}
        raise HTTPException(503,detail=app.state.inference["reason"])

@app.post("/api/runs",status_code=202)
async def start_run(request: RunRequest):
    if request.mode=="live" and not app.state.inference["verified"]:
        raise HTTPException(503,"Verify Crusoe connectivity before a live run; simulated mode is available")
    active = [r for r in await app.state.repo.all() if r["status"] in ("queued","running")]
    if len(active) >= 5:
        raise HTTPException(429,"Five runs already active")
    run = new_run(request.tickers,request.mode)
    await app.state.repo.save(run)
    return {"id":run["id"],"status":run["status"],"mode":run["mode"]}

@app.get("/api/runs")
async def list_runs():
    return [{k:r.get(k) for k in ("id","tickers","mode","status","created_at","stop_reason")}
            for r in await app.state.repo.all()]

async def get_run(run_id):
    run = await app.state.repo.get(run_id)
    if run is None:
        raise HTTPException(404,"Run not found")
    return run

@app.get("/api/runs/{run_id}")
async def read_run(run_id: str):
    run = await get_run(run_id)
    run.pop("source_cache",None)
    return run

@app.get("/api/runs/{run_id}/scenario")
async def scenario(run_id: str, delta_bps: int = 200, assume_unknown_unhedged: bool = False):
    run = await get_run(run_id)
    try:
        return {ticker:rate_scenario([Instrument.model_validate(i) for i in run["instruments"] if i["ticker"]==ticker],
                                    delta_bps,date.today(),assume_unknown_unhedged)
                for ticker in run["tickers"]}
    except ValueError:
        raise HTTPException(422,"Unsupported scenario")

class RefinanceRequest(BaseModel):
    instrument_id: str
    principal_to_refinance: Decimal = Field(ge=0)
    old_rate_pct: Decimal = Field(ge=0,le=100)
    new_rate_pct: Decimal = Field(ge=0,le=100)
    horizon: date

@app.post("/api/runs/{run_id}/refinancing")
async def refinancing(run_id: str, request: RefinanceRequest):
    run = await get_run(run_id)
    candidate = next((i for i in run["instruments"] if i["instrument_id"]==request.instrument_id),None)
    if candidate is None:
        raise HTTPException(422,"A verified instrument is required")
    try:
        return refinancing_scenario(Instrument.model_validate(candidate),request.principal_to_refinance,
                                    request.old_rate_pct,request.new_rate_pct,request.horizon,date.today())
    except ValueError as exc:
        raise HTTPException(422,str(exc))
