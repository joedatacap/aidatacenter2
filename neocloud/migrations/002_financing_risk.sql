-- Additive V2 migration. Authoritative JSONB stays in runs.body via unchanged save/get/all.
-- Read projections avoid changing Neon transport or V1 INSERT column ordering.
CREATE TABLE IF NOT EXISTS schema_migrations (
 version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE OR REPLACE VIEW v2_financing_records AS
 SELECT r.id AS run_id, category.key AS record_type, fact.value->>'id' AS record_id,
        fact.value->>'ticker' AS ticker, fact.value->>'as_of' AS as_of_date,
        fact.value->>'status' AS verification_status, fact.value AS body
 FROM runs r
 CROSS JOIN LATERAL jsonb_each(COALESCE(r.body->'risk','{}'::jsonb)) category
 CROSS JOIN LATERAL jsonb_array_elements(category.value) fact;
CREATE OR REPLACE VIEW v2_model_attempts AS
 SELECT r.id AS run_id, t.value->>'id' AS task_id, t.value->>'role' AS role,
        a.value->>'model' AS model, a.value AS body
 FROM runs r
 CROSS JOIN LATERAL jsonb_array_elements(r.body->'tasks') t
 CROSS JOIN LATERAL jsonb_array_elements(COALESCE(t.value->'inference_attempts','[]'::jsonb)) a;
CREATE INDEX IF NOT EXISTS runs_v2_risk_idx ON runs USING GIN ((body->'risk'));
INSERT INTO schema_migrations(version) VALUES('002_financing_risk') ON CONFLICT(version) DO NOTHING;
