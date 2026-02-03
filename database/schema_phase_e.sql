-- Phase E: Validation Core - Snapshots Table
-- This table stores immutable records of predictions + market odds at the moment of decision.

CREATE TABLE IF NOT EXISTS prediction_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationship (Loose coupling to allow deletion of original records if needed, though unlikely)
    upcoming_match_id UUID, 
    prediction_id UUID,     -- Can look up more details if needed

    -- Event Identity (Denormalized for immutability)
    player_1 TEXT NOT NULL,
    player_2 TEXT NOT NULL,
    tournament TEXT,
    surface TEXT,
    match_date DATE,

    -- Model Context
    model_version TEXT NOT NULL,          -- e.g. "xgb_service_v1"
    engine_used TEXT NOT NULL,            -- e.g. "ml", "heuristic"
    trust_score NUMERIC(4,3),             -- 0.000 - 1.000

    -- Frozen Prediction
    p_match_p1 NUMERIC(4,3) NOT NULL,
    p_match_p2 NUMERIC(4,3) NOT NULL,

    -- Frozen Market (The "Truth" for ROI)
    odds_p1 NUMERIC(6,3) NOT NULL,        -- Decimal format (e.g. 1.85)
    odds_p2 NUMERIC(6,3),

    -- Decision
    side_taken TEXT CHECK (side_taken IN ('P1','P2')),
    stake_unit NUMERIC(5,2) DEFAULT 1.0,   -- Unit sizing (default flat 1.0)

    -- Result (Null initially, filled by result_updater)
    result TEXT CHECK (result IN ('WIN','LOSS','VOID')),
    settled_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS (Public Read for now, similar to other tables)
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON prediction_snapshots
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON prediction_snapshots
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Indexes for Analysis
CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON prediction_snapshots(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_trust_score ON prediction_snapshots(trust_score);
CREATE INDEX IF NOT EXISTS idx_snapshots_model_version ON prediction_snapshots(model_version);
