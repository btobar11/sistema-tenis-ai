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
}

export interface AnalysisPreview {
    id: string;
    match_id: string;
    risk_level: 'low' | 'medium' | 'high';
    confidence_percent: number;
    suggested_pick: string;
}

export const api = {
    async getMatchesToday() {
        const { data, error } = await supabase
            .from('matches')
            .select(`
                *,
                player_a:player1_id(*),
                player_b:player2_id(*)
            `)
            .order('date', { ascending: true })
            .limit(50);

        if (error) throw error;

        // Transform to match expected interface
        return (data || []).map((m: any) => ({
            ...m,
            tournament: m.tournament_name,
            surface: m.surface.charAt(0).toUpperCase() + m.surface.slice(1), // hard -> Hard
            player_a: {
                ...m.player_a,
                ranking: m.player_a?.rank_single || 999
            },
            player_b: {
                ...m.player_b,
                ranking: m.player_b?.rank_single || 999
            },
            score: m.score_full,
            winner_name: m.winner_id ? (m.player_a.id === m.winner_id ? m.player_a.name : m.player_b.name) : null
        })) as Match[];
    },

    async getUpcomingMatches(days: number = 7) {
        const now = new Date();
        // Use UTC dates to match database timestamps
        const startDate = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
        const endDate = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + days - 1, 23, 59, 59));

        const { data, error } = await supabase
            .from('matches')
            .select(`
                *,
                player_a:player1_id(*),
                player_b:player2_id(*)
            `)
            .gte('date', startDate.toISOString())
            .lte('date', endDate.toISOString())
            .order('date', { ascending: true });

        if (error) throw error;

        return (data || []).map((m: any) => ({
            ...m,
            tournament: m.tournament_name,
            surface: m.surface.charAt(0).toUpperCase() + m.surface.slice(1),
            player_a: {
                ...m.player_a,
                ranking: m.player_a?.rank_single || 999
            },
            player_b: {
                ...m.player_b,
                ranking: m.player_b?.rank_single || 999
            },
            score: m.score_full,
            winner_name: m.winner_id ? (m.player_a.id === m.winner_id ? m.player_a.name : m.player_b.name) : null
        })) as Match[];
    },

    async getMatchAnalysis(matchId: string) {
        const { data, error } = await supabase
            .from('analysis_results')
            .select('*')
            .eq('match_id', matchId)
            .single();

        if (error && error.code !== 'PGRST116') throw error;
        return data as AnalysisPreview;
    },

    async getRiskColor(level: string) {
        switch (level) {
            case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
            case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
            case 'high': return 'text-red-400 bg-red-500/10 border-red-500/20';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    },

    // -- PROFESSIONAL STATS ENGINE -- //

    async getPlayerHistory(playerId: string, limit = 50) {
        const { data, error } = await supabase
            .from('matches')
            .select('*')
            .or(`player1_id.eq.${playerId},player2_id.eq.${playerId}`)
            .order('date', { ascending: false })
            .limit(limit);

        if (error) {
            console.error("Error fetching history:", error);
            return [];
        }

        // Transform data to include winner_name for metrics calculation
        return (data || []).map((m: any) => ({
            ...m,
            score: m.score_full,
            surface: m.surface
        }));
    },

    async getHeadToHead(playerAId: string, playerBId: string) {
        const { data, error } = await supabase
            .from('matches')
            .select('*')
            .or(`and(player1_id.eq.${playerAId},player2_id.eq.${playerBId}),and(player1_id.eq.${playerBId},player2_id.eq.${playerAId})`)
            .order('date', { ascending: false });

        if (error) {
            console.error("Error fetching H2H:", error);
            return [];
        }

        return (data || []).map((m: any) => ({
            ...m,
            score: m.score_full
        }));
    },

    async searchPlayers(query: string) {
        if (!query || query.length < 2) return [];

        const { data, error } = await supabase
            .from('players')
            .select('*')
            .ilike('name', `%${query}%`)
            .limit(10);

        if (error) {
            console.error("Error searching players:", error);
            return [];
        }

        return data || [];
    },

    calculatePlayerMetrics(_playerId: string, playerName: string, history: any[], targetSurface: string) {
        if (!history || history.length === 0) {
            return {
                winrateSurface: 0.5,
                form: 0.5,
                regularity: 0.5,
                h2h: 0.5,
                setTrend: 0.5
            };
        }

        // Helper: Determine if player won
        const didPlayerWin = (match: any): boolean => {
            const winnerName = match.winner_name;
            if (!winnerName) return false;
            return winnerName.toLowerCase().includes(playerName.toLowerCase()) ||
                playerName.toLowerCase().includes(winnerName.toLowerCase());
        };

        // --- 1. SURFACE WIN RATE (Bayesian Smoothing) ---
        const surfaceMatches = history.filter(m =>
            m.surface && m.surface.toLowerCase() === targetSurface.toLowerCase()
        );

        let surfaceWins = 0;
        surfaceMatches.forEach(m => {
            if (didPlayerWin(m)) surfaceWins++;
        });

        // Beta(α=2, β=2) prior for regularization
        const alpha = 2;
        const beta = 2;
        const winrateSurface = surfaceMatches.length > 0
            ? (surfaceWins + alpha) / (surfaceMatches.length + alpha + beta)
            : 0.5;

        // --- 2. FORM (Exponentially Weighted Recent Performance) ---
        const recentHistory = history.slice(0, 15);
        let weightedWins = 0;
        let totalWeight = 0;
        const lambda = 0.15; // Decay rate

        recentHistory.forEach((m, idx) => {
            const weight = Math.exp(-lambda * idx);
            totalWeight += weight;
            if (didPlayerWin(m)) weightedWins += weight;
        });

        const form = totalWeight > 0 ? (weightedWins / totalWeight) : 0.5;

        // --- 3. REGULARITY (Consistency via Coefficient of Variation) ---
        const windowSize = 5;
        const winRates: number[] = [];

        for (let i = 0; i <= history.length - windowSize; i++) {
            const window = history.slice(i, i + windowSize);
            const windowWins = window.filter(m => didPlayerWin(m)).length;
            winRates.push(windowWins / windowSize);
        }

        const regularity = winRates.length > 0 ? (() => {
            const mean = winRates.reduce((a, b) => a + b, 0) / winRates.length;
            const variance = winRates.reduce((sum, rate) => sum + Math.pow(rate - mean, 2), 0) / winRates.length;
            const stdDev = Math.sqrt(variance);
            const cv = mean > 0.01 ? stdDev / mean : 0;
            return 1 - Math.min(cv, 1.0);
        })() : 0.7;

        // --- 4. SET TREND (Set-Level Performance Analysis) ---
        let totalSets = 0;
        let setsWon = 0;

        history.slice(0, 10).forEach(m => {
            const score = m.score;
            if (!score) return;

            const sets = score.split(' ').filter((s: string) => s.includes('-'));
            const playerWonMatch = didPlayerWin(m);

            sets.forEach((set: string) => {
                const [a, b] = set.split('-').map(Number);
                if (isNaN(a) || isNaN(b)) return;

                totalSets++;
                const setWinner = a > b;

                // Simplified set attribution
                if (playerWonMatch && setWinner) setsWon++;
                if (!playerWonMatch && !setWinner) setsWon++;
            });
        });

        const setTrend = totalSets > 0 ? (setsWon / totalSets) : 0.5;

        return {
            winrateSurface,
            form,
            regularity,
            h2h: 0.5, // Calculated separately
            setTrend
        };
    }
};
