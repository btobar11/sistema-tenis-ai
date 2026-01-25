-- Create ELO ratings table to track player performance by surface
CREATE TABLE IF NOT EXISTS elo_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    surface TEXT NOT NULL, -- 'HARD', 'CLAY', 'GRASS', 'OVERALL'
    rating INTEGER DEFAULT 1500,
    matches_played INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, surface)
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_elo_player_surface ON elo_ratings(player_id, surface);
