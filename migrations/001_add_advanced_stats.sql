
-- Migration: Add Advanced Stats Tables
-- Description: Adds tables for match statistics, set scores, and historical player performance.

-- 1. Match Statistics (Detailed stats per match)
CREATE TABLE IF NOT EXISTS public.match_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES public.matches(id) ON DELETE CASCADE,
    
    -- Player 1 Stats
    aces_p1 INT DEFAULT 0,
    df_p1 INT DEFAULT 0,
    first_serve_p1 INT DEFAULT 0, -- Percentage or Count? Usually Percentage in simple scraping
    first_serve_points_won_p1 INT DEFAULT 0,
    second_serve_points_won_p1 INT DEFAULT 0,
    break_points_saved_p1 INT DEFAULT 0,
    break_points_faced_p1 INT DEFAULT 0,
    total_points_won_p1 INT DEFAULT 0,
    
    -- Player 2 Stats
    aces_p2 INT DEFAULT 0,
    df_p2 INT DEFAULT 0,
    first_serve_p2 INT DEFAULT 0,
    first_serve_points_won_p2 INT DEFAULT 0,
    second_serve_points_won_p2 INT DEFAULT 0,
    break_points_saved_p2 INT DEFAULT 0,
    break_points_faced_p2 INT DEFAULT 0,
    total_points_won_p2 INT DEFAULT 0,
    
    duration_minutes INT, -- For fatigue calculation
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Set Scores (Granular scoring)
CREATE TABLE IF NOT EXISTS public.set_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES public.matches(id) ON DELETE CASCADE,
    set_number INT NOT NULL, -- 1, 2, 3, 4, 5
    score_p1 INT NOT NULL,
    score_p2 INT NOT NULL,
    tiebreak_score INT, -- Points in tiebreak for the loser, or winner? Usually just the loser score implies tiebreak
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Player History (Aggregate performance cache)
-- This table stores a summary of a player's performance up to a certain date, 
-- allowing fast lookup of "Form in last 20 matches".
CREATE TABLE IF NOT EXISTS public.player_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES public.players(id) ON DELETE CASCADE,
    match_id UUID REFERENCES public.matches(id), -- Link to the match that generated this history point
    match_date DATE NOT NULL,
    
    opponent_id UUID REFERENCES public.players(id),
    result TEXT CHECK (result IN ('Win', 'Loss')),
    
    surface TEXT,
    opponent_rank INT,
    
    -- Rolling metrics at this point in time
    elo_at_match INT,
    form_last_20_wins INT, -- Cached count of wins in prev 20 matches
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON public.match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_set_scores_match_id ON public.set_scores(match_id);
CREATE INDEX IF NOT EXISTS idx_player_history_player_date ON public.player_history(player_id, match_date);
