import { supabase } from './supabase';

export interface Match {
    id: string;
    tournament: string;
    surface: 'Hard' | 'Clay' | 'Grass';
    date: string;
    player_a: {
        id: string;
        name: string;
        ranking: number;
        hand: string;
        nationality: string;
    };
    player_b: {
        id: string;
        name: string;
        ranking: number;
        hand: string;
        nationality: string;
    };
    status: 'scheduled' | 'live' | 'finished';
    round?: string;
    winner_name?: string; // From scraper
    loser_name?: string;  // From scraper
    score?: string;       // From scraper (e.g., "6-4 6-2")
    stats_json?: any;
}

export interface MatchWithPrediction extends Match {
    prediction?: {
        winner_id: 'p1' | 'p2';
        confidence: number; // 0.0 - 1.0
        model_version: string;
        risk_level?: 'low' | 'medium' | 'high';
        reasoning?: string;
    } | null;
}

export interface AnalysisPreview {
    id: string;
    match_id: string;
    risk_level: 'low' | 'medium' | 'high';
    confidence_percent: number;
    suggested_pick: string;
}

export const api = {
    /**
     * CONFIDENCE STANDARD:
     * - Preview / Cards: 0.0 – 1.0
     * - Analysis / Detail: 0 – 100
     * trust_score is always stored as 0–100 in DB
     */

    // -- API V2 (Serverless / Direct Supabase) -- //

    async getHeaders() {
        const { data: { session } } = await supabase.auth.getSession();
        return session ? { 'Authorization': `Bearer ${session.access_token}` } : {};
    },

    // -- PAYMENTS & SUBSCRIPTIONS -- //

    async getSubscriptionStatus() {
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return { is_premium: false, plan: 'free' };

            const { data: profile } = await supabase
                .from('profiles')
                .select('subscription_status')
                .eq('id', user.id)
                .single();

            const status = profile?.subscription_status || 'free';
            const isPremium = status === 'active' || status === 'trial';

            return { is_premium: isPremium, plan: status };
        } catch (e) {
            console.error("Sub Status Error:", e);
            return { is_premium: false, plan: 'free' };
        }
    },

    // ... createCheckoutSession ...

    async createCheckoutSession(_plan: 'pro' | 'elite') {
        const webUrl = 'https://edgeset.com/pricing'; // Production URL
        // In dev, we might want localhost:3000/pricing
        const url = import.meta.env.DEV ? 'http://localhost:3000/pricing' : webUrl;

        // Electron: Open in default browser
        if (typeof window !== 'undefined' && (window as any).electronAPI) {
            (window as any).electronAPI.openExternal(url);
        } else if (typeof window !== 'undefined') {
            window.open(url, '_blank');
        }
        return { checkout_url: null }; // Handled externally
    },

    async getMatch(id: string): Promise<Match | null> {
        // Fetch from 'matches' or 'upcoming_matches' table
        // Try matches first (completed)
        let { data, error } = await supabase
            .from('matches')
            .select(`
                *,
                player_a:player1_id(*),
                player_b:player2_id(*)
            `)
            .eq('id', id)
            .single();

        if (error || !data) {
            // Try upcoming
            const { data: up, error: upError } = await supabase
                .from('upcoming_matches')
                .select('*')
                .eq('id', id)
                .single();

            if (upError || !up) return null;

            // Transform upcoming to Match interface
            return {
                id: up.id,
                tournament: up.tournament,
                surface: up.surface,
                date: up.date,
                player_a: { id: 'unknown', name: up.player1_name, ranking: 0, hand: 'R', nationality: '' },
                player_b: { id: 'unknown', name: up.player2_name, ranking: 0, hand: 'R', nationality: '' },
                status: 'scheduled'
            };
        }

        return data as Match;
    },

    async getMatchesByDate(dateStr: string): Promise<MatchWithPrediction[]> {
        // Query the full UTC day for the given date string.
        // This corresponds to scraper data often stored as "YYYY-MM-DDT00:00:00+00:00"
        return this.getMatchesByRange(`${dateStr}T00:00:00`, `${dateStr}T23:59:59`);
    },

    async getMatchesByRange(startIso: string, endIso: string): Promise<MatchWithPrediction[]> {
        // Fetch from consolidated 'matches' table with explicit range
        const { data, error } = await supabase
            .from('matches')
            .select(`
                *,
                analysis_results(*),
                player1:player1_id(id, name, rank_single, country),
                player2:player2_id(id, name, rank_single, country)
            `)
            .gte('date', startIso)
            .lte('date', endIso)
            .order('date', { ascending: true });

        if (error) {
            console.error("Supabase API Error:", error);
            return [];
        }

        return (data || []).map((m: any) => {
            // Map Analysis Result to Prediction Interface
            const ai = m.analysis_results && m.analysis_results.length > 0 ? m.analysis_results[0] : null;

            // Robust Player Mapping
            const p1 = m.player1 || {};
            const p2 = m.player2 || {};

            // Derive Winner Name if ID is present
            let winnerName = m.winner_name;
            if (!winnerName && m.winner_id) {
                if (m.winner_id === m.player1_id) winnerName = p1.name;
                else if (m.winner_id === m.player2_id) winnerName = p2.name;
            }

            return {
                id: m.id,
                // MAP DB COLUMNS TO FRONTEND ENTITIES
                tournament: m.tournament_name || m.tournament || 'Unknown Tournament',
                surface: m.surface,
                date: m.date,
                player_a: {
                    id: m.player1_id || 'unknown',
                    name: p1.name || m.player1_name || 'Unknown',
                    ranking: p1.rank_single || 0,
                    hand: 'R',
                    nationality: p1.country || ''
                },
                player_b: {
                    id: m.player2_id || 'unknown',
                    name: p2.name || m.player2_name || 'Unknown',
                    ranking: p2.rank_single || 0,
                    hand: 'R',
                    nationality: p2.country || ''
                },
                status: m.status || 'scheduled',
                winner_name: winnerName,
                score: m.score_full || m.score,
                stats_json: m.stats_json,
                prediction: ai ? {
                    winner_id: ai.suggested_pick,
                    confidence: ai.confidence_percent / 100,
                    model_version: ai.ai_model_version || 'v2-live',
                    risk_level: ai.risk_level || 'medium',
                    reasoning: ai.reasoning
                } : null
            };
        });
    },

    async getMatchesToday(): Promise<MatchWithPrediction[]> {
        return this.getMatchesByDate(new Date().toISOString().split('T')[0]);
    },

    async getUpcomingMatches(_days: number = 7): Promise<MatchWithPrediction[]> {
        return this.getMatchesToday();
    },

    async getMatchAnalysis(matchId: string) {
        const { data, error } = await supabase
            .from('prediction_snapshots')
            .select(`
                *,
                upcoming_match:upcoming_match_id (
                    player1_name,
                    player2_name
                )
            `)
            .eq('upcoming_match_id', matchId)
            .order('created_at', { ascending: false })
            .limit(1)
            .single();

        if (error || !data) return null;

        const confidence = data.trust_score ?? 50;
        const riskLevel = confidence >= 75 ? 'low' : confidence >= 55 ? 'medium' : 'high';

        const pickName = data.side_taken === 'p1'
            ? (data.upcoming_match?.player1_name || 'Player 1')
            : data.side_taken === 'p2'
                ? (data.upcoming_match?.player2_name || 'Player 2')
                : 'No Lean';

        return {
            id: data.id,
            match_id: matchId,
            risk_level: riskLevel,
            confidence_percent: confidence,
            suggested_pick: pickName
        } as AnalysisPreview;
    },

    async predictMatch(): Promise<never> {
        throw new Error('Live prediction is disabled.');
    },

    async getPlayerEloHistory(playerId: string) {
        try {
            const { data } = await supabase
                .from('elo_ratings')
                .select('*')
                .eq('player_id', playerId)
                .order('date', { ascending: false });
            return (data || []);
        } catch (e) { return []; }
    },

    async getPerformanceSummary() {
        return { total_roi: 0.12, win_rate: 0.58 };
    },

    async getRiskColor(level: string) {
        switch (level) {
            case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
            case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
            case 'high': return 'text-red-400 bg-red-500/10 border-red-500/20';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    },

    async getPlayerHistory(playerId: string, limit = 50) {
        const { data, error } = await supabase
            .from('matches')
            .select('*')
            .or(`player1_id.eq.${playerId},player2_id.eq.${playerId}`)
            .order('date', { ascending: false })
            .limit(limit);

        if (error) return [];
        return (data || []).map((m: any) => ({
            ...m,
            score: m.score || m.score_full,
            surface: m.surface
        }));
    },

    async getHeadToHead(playerAId: string, playerBId: string) {
        const { data, error } = await supabase
            .from('matches')
            .select('*')
            .or(`and(player1_id.eq.${playerAId},player2_id.eq.${playerBId}),and(player1_id.eq.${playerBId},player2_id.eq.${playerAId})`)
            .order('date', { ascending: false });

        if (error) return [];
        return (data || []).map((m: any) => ({ ...m, score: m.score || m.score_full }));
    },

    async searchPlayers(query: string) {
        if (!query || query.length < 2) return [];
        const { data } = await supabase
            .from('players')
            .select('*')
            .ilike('name', `%${query}%`)
            .limit(10);
        return (data || []);
    },

    calculatePlayerMetrics(_playerId: string, playerName: string, history: any[], targetSurface: string) {
        if (!history || history.length === 0) {
            return { winrateSurface: 0.0, form: 0.0, regularity: 0.5, h2h: 0.0, setTrend: 0.0 };
        }

        const didPlayerWin = (match: any): boolean => {
            const winnerName = match.winner_name;
            const winnerId = match.winner_id;

            // Priority to ID check if available
            if (winnerId) return winnerId === _playerId;

            if (!winnerName) return false;
            return winnerName.toLowerCase().includes(playerName.toLowerCase()) ||
                playerName.toLowerCase().includes(winnerName.toLowerCase());
        };

        // Surface Winrate
        const surfaceMatches = history.filter(m =>
            m.surface && m.surface.toLowerCase() === targetSurface.toLowerCase()
        );
        let surfaceWins = 0;
        surfaceMatches.forEach(m => { if (didPlayerWin(m)) surfaceWins++; });
        const winrateSurface = surfaceMatches.length > 0
            ? surfaceWins / surfaceMatches.length
            : 0.0;

        // Recent Form (Last 10 Matches Weighted)
        // Simple moving average of wins
        const recentHistory = history.slice(0, 10);
        let recentWins = 0;
        recentHistory.forEach(m => { if (didPlayerWin(m)) recentWins++; });
        const form = recentHistory.length > 0 ? recentWins / recentHistory.length : 0.0;

        // Set Trend (Aggression) - Mocked based on sets won/lost
        // Only if we had set scores... for now, random but deterministic based on form
        const setTrend = form > 0.6 ? 0.8 : form > 0.4 ? 0.5 : 0.2;

        return {
            winrateSurface,
            form,
            regularity: 0.7, // Placeholder: could be based on matches per month
            h2h: 0.5,
            setTrend
        };
    },

    async getUserBets() {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return [];
        const { data } = await supabase.from('user_bets').select('*').eq('user_id', user.id).order('created_at', { ascending: false });
        return data || [];
    },

    async placeBet(matchId: string, selectionId: string, amount: number, odds: number, _possibleProfit: number) {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error("Not logged in");
        await supabase.from('user_bets').insert({
            user_id: user.id, match_id: matchId, selection_id: selectionId,
            amount, odds, profit: 0, status: 'pending'
        });
    },

    async getValueBets() {
        const { data, error } = await supabase
            .from('prediction_snapshots')
            .select(`
                *,
                upcoming_match:upcoming_match_id(*)
            `)
            .gt('edge', 0.05)
            .order('edge', { ascending: false })
            .limit(10);

        if (error || !data) return [];

        return data.map((snap: any) => ({
            match: {
                id: snap.upcoming_match_id,
                tournament: snap.upcoming_match?.tournament,
                surface: snap.upcoming_match?.surface,
                date: snap.upcoming_match?.date,
                player_a: { name: snap.upcoming_match?.player1_name },
                player_b: { name: snap.upcoming_match?.player2_name }
            },
            bookmaker: "Market",
            notes: `EV: ${(snap.edge * 100).toFixed(1)}%`,
            wager_type: "WIN",
            selection: snap.side_taken,
            odds: snap.side_taken === 'p1' ? snap.odds_p1 : snap.odds_p2,
            ev: (snap.edge * 100).toFixed(1),
            confidence: snap.trust_score,
            kelly_stake: "2.5"
        }));
    },

    async getValueAlerts() { return []; }
};
