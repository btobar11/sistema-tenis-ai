ALTER FUNCTION public.get_player_win_rate(uuid, surface_type) SET search_path = public;
ALTER FUNCTION public.get_player_form(uuid, integer) SET search_path = public;
ALTER FUNCTION public.get_player_fatigue(uuid, integer) SET search_path = public;
ALTER FUNCTION public.update_player_stats(uuid) SET search_path = public;
ALTER FUNCTION public.generate_match_checklist(uuid) SET search_path = public;
ALTER FUNCTION public.generate_prediction(uuid) SET search_path = public;

-- 2. Performance: create indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_analysis_results_suggested_pick ON public.analysis_results(suggested_pick);
CREATE INDEX IF NOT EXISTS idx_player_history_match_id ON public.player_history(match_id);
CREATE INDEX IF NOT EXISTS idx_player_history_opponent_id ON public.player_history(opponent_id);
CREATE INDEX IF NOT EXISTS idx_predictions_checklist_id ON public.predictions(checklist_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match_id ON public.predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_upcoming_matches_player1_id ON public.upcoming_matches(player1_id);
CREATE INDEX IF NOT EXISTS idx_upcoming_matches_player2_id ON public.upcoming_matches(player2_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_match_id ON public.user_bets(match_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_user_id ON public.user_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_value_alerts_match_id ON public.value_alerts(match_id);

-- 3. Performance: Drop duplicate index
-- Assuming idx_match_stats_match_id and idx_stats_match_id are checking the same thing.
DROP INDEX IF EXISTS public.idx_match_stats_match_id;

-- 4. Security: Enable RLS and add basic policies
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.api_keys USING (true) WITH CHECK (true);

ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.usage_logs USING (true) WITH CHECK (true);

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.subscriptions USING (true) WITH CHECK (true);

ALTER TABLE public.elo_ratings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.elo_ratings USING (true) WITH CHECK (true);

ALTER TABLE public.match_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.match_stats USING (true) WITH CHECK (true);

ALTER TABLE public.value_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.value_alerts USING (true) WITH CHECK (true);

ALTER TABLE public.player_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.player_history USING (true) WITH CHECK (true);

ALTER TABLE public.market_odds ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.market_odds USING (true) WITH CHECK (true);

ALTER TABLE public.set_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.set_scores USING (true) WITH CHECK (true);

ALTER TABLE public.prediction_ledger ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Baseline Access" ON public.prediction_ledger USING (true) WITH CHECK (true);
