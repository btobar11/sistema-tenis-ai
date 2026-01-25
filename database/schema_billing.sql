
-- Tabla de Logs de Uso para Facturación (Audit Trail)
-- Cada request se guarda aquí. En alta escala, esto iría a ClickHouse o TimescaleDB.
-- Para MVP, Postgres particionado o simple funciona bien hasta ~1M requests.

CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL, -- "AcmeFund"
    api_key_prefix TEXT NOT NULL, -- "sk_live_1234"
    
    endpoint TEXT NOT NULL, -- "/inference/predict"
    method TEXT NOT NULL, -- "POST"
    status_code INTEGER NOT NULL, -- 200, 400, 500
    
    cost_units INTEGER DEFAULT 1, -- 1 unit for GET, 10 for Predict?
    processing_time_ms INTEGER,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indices para reportes rápidos
CREATE INDEX IF NOT EXISTS idx_usage_org_date ON usage_logs(organization_id, timestamp);
