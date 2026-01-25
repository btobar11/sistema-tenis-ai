
-- Tabla de Alertas de Valor (Resultado del Value Engine)
CREATE TABLE IF NOT EXISTS value_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id), -- Puede ser nulo si no hubo mapping exitoso
    
    -- Metadata del Partido
    player_home TEXT NOT NULL,
    player_away TEXT NOT NULL,
    tournament TEXT,
    date TIMESTAMP WITH TIME ZONE,
    
    -- Datos del Análisis
    bookmaker TEXT NOT NULL,
    selection TEXT NOT NULL, -- 'Home' o 'Away' (o nombre jugador)
    market_price NUMERIC(5, 2) NOT NULL, -- Cuota
    model_probability NUMERIC(5, 4) NOT NULL, -- 0.7500
    
    -- El Santo Grial
    ev_percentage NUMERIC(6, 2) NOT NULL, -- e.g. 15.20 (%)
    kelly_stake NUMERIC(4, 2), -- % de bankroll sugerido
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' -- active, expired, won, lost
);

CREATE INDEX IF NOT EXISTS idx_value_alerts_date ON value_alerts(date);
CREATE INDEX IF NOT EXISTS idx_value_alerts_ev ON value_alerts(ev_percentage);
