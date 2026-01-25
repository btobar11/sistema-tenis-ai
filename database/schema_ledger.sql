
-- Ledger Inmutable de Predicciones (The Source of Truth)
-- Este registro NUNCA debe ser modificado, solo añadido (Append-Only).
CREATE TABLE IF NOT EXISTS prediction_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id),
    
    -- Snapshot del Momento
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Datos del Modelo
    prob_p1 NUMERIC(5, 4) NOT NULL,
    prob_p2 NUMERIC(5, 4) NOT NULL,
    model_version TEXT NOT NULL, -- e.g. "xgb_v2.1"
    
    -- Datos del Mercado (Snapshot)
    bookmaker TEXT NOT NULL,
    home_odds NUMERIC(5, 2),
    away_odds NUMERIC(5, 2),
    
    -- Decisión del Sistema
    selected_pick TEXT, -- 'player_a' or 'player_b' or 'skip'
    ev_calculated NUMERIC(6, 2),
    stake_suggested NUMERIC(4, 2), -- Kelly stake
    
    -- Resultado (Fill later via Oracle)
    result_status TEXT DEFAULT 'pending', -- pending, won, lost, void
    profit_loss NUMERIC(8, 2) DEFAULT 0,
    
    CONSTRAINT immutable_record CHECK (true) -- Placeholder for conceptual constraint
);

CREATE INDEX IF NOT EXISTS idx_ledger_date ON prediction_ledger(prediction_date);
CREATE INDEX IF NOT EXISTS idx_ledger_status ON prediction_ledger(result_status);
