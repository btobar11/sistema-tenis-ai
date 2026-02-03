-- Match Statistics Table (Level 1 Data) - REFINED
-- Stores granular performance metrics for each player in a match.
-- NOW storing RAW COUNTS to preserve variance and statistical weight.

CREATE TABLE IF NOT EXISTS match_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    
    -- Service Raw Counts (The Source of Truth)
    service_points_won INT,
    service_points_played INT,
    
    first_serves_in INT,
    first_serves_total INT,
    
    first_serve_points_won INT,
    first_serve_points_played INT,
    
    second_serve_points_won INT,
    second_serve_points_played INT,
    
    -- Return Raw Counts
    return_points_won INT,
    return_points_played INT,
    
    -- Pressure / Break Points
    break_points_saved INT DEFAULT 0,
    break_points_faced INT DEFAULT 0,
    break_points_converted INT DEFAULT 0,
    break_points_opportunities INT DEFAULT 0,
    
    -- Meta / Fatigue
    aces INT DEFAULT 0,
    double_faults INT DEFAULT 0,
    service_games_played INT DEFAULT 0,
    match_duration_minutes INT,
    total_points_played INT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT DEFAULT 'tennis_explorer',
    
    CONSTRAINT unique_match_player_stats UNIQUE (match_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_stats_match_id ON match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_stats_player_id ON match_stats(player_id);

-- Optional: Views to calculate percentages on the fly
-- CREATE VIEW view_player_stats_pct AS ...
