CREATE TABLE IF NOT EXISTS runs (
 id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), body JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS companies (
 ticker TEXT PRIMARY KEY, name TEXT NOT NULL, base_currency TEXT NOT NULL,
 sector TEXT NOT NULL, url TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 parent_task_id TEXT REFERENCES tasks(id), ticker TEXT,
 role TEXT NOT NULL, status TEXT NOT NULL, retries INTEGER NOT NULL DEFAULT 0,
 body JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS tasks_parent_idx ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS tasks_run_status_idx ON tasks(run_id,status);
CREATE INDEX IF NOT EXISTS tasks_ticker_idx ON tasks(ticker);
CREATE TABLE IF NOT EXISTS agent_events (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 task_id TEXT REFERENCES tasks(id), created_at TIMESTAMPTZ NOT NULL, body JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 source_url TEXT NOT NULL, retrieved_at TIMESTAMPTZ NOT NULL, body JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS instruments (
 run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 instrument_id TEXT NOT NULL, ticker TEXT NOT NULL REFERENCES companies(ticker),
 outstanding_principal NUMERIC, currency TEXT NOT NULL, snapshot_date DATE, body JSONB NOT NULL,
 PRIMARY KEY(run_id,instrument_id)
);
CREATE INDEX IF NOT EXISTS instruments_ticker_idx ON instruments(ticker);
CREATE TABLE IF NOT EXISTS customer_deals (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 ticker TEXT NOT NULL REFERENCES companies(ticker), body JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS deal_financing_links (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 body JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS market_observations (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
 ticker_or_security TEXT NOT NULL, observation_date DATE NOT NULL,
 metric_type TEXT NOT NULL, value NUMERIC NOT NULL, body JSONB NOT NULL
);
