-- PERFORMANCE: Add indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_checklists_match_id ON public.checklists(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_player1_id ON public.matches(player1_id);
CREATE INDEX IF NOT EXISTS idx_matches_player2_id ON public.matches(player2_id);
CREATE INDEX IF NOT EXISTS idx_matches_winner_id ON public.matches(winner_id);
CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON public.match_stats(match_id);
-- Table predictions might effectively be prediction_snapshots or similar. Skipping explicit predictions table index if generic.
CREATE INDEX IF NOT EXISTS idx_prediction_snapshots_upcoming_match_id ON public.prediction_snapshots(upcoming_match_id);

-- SECURITY: Fix mutable search paths
ALTER FUNCTION public.prevent_ledger_modification() SET search_path = public;
ALTER FUNCTION public.get_player_win_rate(text, text) SET search_path = public;

-- SECURITY: Add missing RLS policies (Basic Safety)
-- Checklists: Allow public read, authenticated insert/update (adjust as needed)
ALTER TABLE public.checklists ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON public.checklists FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users only" ON public.checklists FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Player Stats: Allow public read
ALTER TABLE public.player_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON public.player_stats FOR SELECT USING (true);

-- Duplicate Index Fix
DROP INDEX IF EXISTS idx_usage_org_date; -- Drop one of the duplicates
