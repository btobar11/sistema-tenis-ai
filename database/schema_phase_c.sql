-- 1. Create Upcoming Matches Table
CREATE TABLE IF NOT EXISTS upcoming_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player1_id UUID REFERENCES players(id),
    player2_id UUID REFERENCES players(id),
    player1_name TEXT,
    player2_name TEXT,
    tournament TEXT,
    surface TEXT,
    round TEXT,
    match_date TIMESTAMP WITH TIME ZONE,
    source TEXT DEFAULT 'TennisExplorer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    CONSTRAINT unique_upcoming_match UNIQUE (player1_name, player2_name, match_date, tournament)
);

-- 2. Create Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upcoming_match_id UUID REFERENCES upcoming_matches(id) ON DELETE CASCADE,
    model_version TEXT,
    engine_used TEXT,
    p_serve_p1 NUMERIC(4,3),
    p_serve_p2 NUMERIC(4,3),
    p_match_p1 NUMERIC(4,3),
    p_match_p2 NUMERIC(4,3),
    p_2_0 NUMERIC(4,3),
    p_2_1 NUMERIC(4,3),
    avg_total_games NUMERIC(5,2),
    surface TEXT,
    tournament TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT unique_prediction_snapshot UNIQUE (upcoming_match_id, model_version, created_at)
);

-- 3. Enable Access (RLS)
-- Allow read/write for now
ALTER TABLE upcoming_matches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read/write for all" ON upcoming_matches FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read/write for all" ON predictions FOR ALL USING (true) WITH CHECK (true);
