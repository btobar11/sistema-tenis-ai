
-- Tabla para almacenar cuotas de mercado (Snapshot por bookmaker)
CREATE TABLE IF NOT EXISTS market_odds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id), -- Link opcional si ya tenemos el match, o usar external_id
    provider_match_id TEXT, -- ID del proveedor (The-Odds-API)
    bookmaker TEXT NOT NULL, -- 'pinnacle', 'bet365'
    player_home TEXT,
    player_away TEXT,
    price_home NUMERIC(5, 2), -- Cuota decimal (e.g. 1.85)
    price_away NUMERIC(5, 2),
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_live BOOLEAN DEFAULT FALSE
);

-- Indice para búsquedas rápidas por partido y proveedor
CREATE INDEX IF NOT EXISTS idx_market_odds_match ON market_odds(match_id, bookmaker);
CREATE INDEX IF NOT EXISTS idx_market_odds_extracted ON market_odds(extracted_at);
