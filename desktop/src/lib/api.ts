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

export interface AnalysisPreview {
    id: string;
    match_id: string;
    risk_level: 'low' | 'medium' | 'high';
    confidence_percent: number;
    suggested_pick: string;
}

export const api = {
    // -- API V2 (Python Backend) -- //
    baseUrl: 'http://localhost:8000',

    async getHeaders() {
        const { data: { session } } = await supabase.auth.getSession();
        const headers: HeadersInit = {
            'Content-Type': 'application/json'
        };
        if (session?.access_token) {
            headers['Authorization'] = `Bearer ${session.access_token}`;
        }
        return headers;
    },

    // -- PAYMENTS & SUBSCRIPTIONS -- //

    async createCheckoutSession(plan: 'pro' | 'elite') {
        try {
            const res = await fetch(`${this.baseUrl}/payments/create-checkout`, {
                method: 'POST',
                headers: await this.getHeaders(),
                body: JSON.stringify({ plan })
            });
            if (!res.ok) throw new Error("Checkout creation failed");
            return await res.json(); // { checkout_url: ... }
        } catch (e) {
            console.error("Payment Error:", e);
            return null;
        }
    },

    async getSubscriptionStatus() {
        try {
            const res = await fetch(`${this.baseUrl}/payments/status`, {
                headers: await this.getHeaders()
            });
            if (!res.ok) return { is_premium: false, plan: 'free' };
            return await res.json();
        } catch (e) {
            console.error("Sub Status Error:", e);
            return { is_premium: false, plan: 'free' };
        }
    },

    async getMatch(id: string): Promise<Match | null> {
        try {
            const res = await fetch(`${this.baseUrl}/matches/${id}`);
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            console.error("API Error:", e);
            return null;
        }
    },

    async getMatchesToday() {
        try {
            // Fetch from Python API
            const res = await fetch(`${this.baseUrl}/matches/?limit=50`);
            if (!res.ok) throw new Error("Failed to fetch matches");
            const data = await res.json();
            return data as Match[];
        } catch (e) {
            console.error("API Error:", e);
            return [];
        }
    },

    async getUpcomingMatches(_days: number = 7) {
        // Calculate date range for API query if needed, or just let API handle default
        // For now, simplify to just fetching recent/upcoming
        try {
            const res = await fetch(`${this.baseUrl}/matches/?limit=100`);
            if (!res.ok) throw new Error("Failed to fetch upcoming");
            return await res.json() as Match[];
        } catch (e) {
            console.error("API Error:", e);
            return [];
        }
    },

    async getMatchAnalysis(matchId: string) {
        // ... legacy fallback ...
        const { data, error } = await supabase
            .from('analysis_results')
            .select('*')
            .eq('match_id', matchId)
            .single();

        if (error && error.code !== 'PGRST116') throw error;
        return data as AnalysisPreview;
    },

    async predictMatch(player1Id: string, player2Id: string) {
        try {
            const res = await fetch(`${this.baseUrl}/inference/predict`, {
                method: 'POST',
                headers: await this.getHeaders(),
                body: JSON.stringify({ player1_id: player1Id, player2_id: player2Id })
            });
            if (!res.ok) throw new Error("Inference failed");
            return await res.json();
        } catch (e) {
            console.error("API Error:", e);
            return null;
        }
    },

    async getPlayerEloHistory(playerId: string) {
        try {
            const res = await fetch(`${this.baseUrl}/players/${playerId}/elo-history`);
            if (!res.ok) return [];
            return await res.json();
        } catch (e) {
            console.error("API Error:", e);
            return [];
        }
    },

    async getPerformanceSummary() {
        try {
            const res = await fetch(`${this.baseUrl}/performance/summary`);
            if (!res.ok) throw new Error("Performance API failed");
            return await res.json();
        } catch (e) {
            console.error("API Error:", e);
            return null;
        }
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
    },

    // -- BETTING JOURNAL -- //

    async getUserBets() {
        // Requires 'user_bets' table
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return [];

        const { data, error } = await supabase
            .from('user_bets')
            .select(`
                *,
                match:match_id (
                    tournament_name,
                    player1_id,
                    player2_id,
                    winner_id,
                    player_a:player1_id(name),
                    player_b:player2_id(name)
                )
            `)
            .eq('user_id', user.id)
            .order('created_at', { ascending: false });

        if (error) {
            console.error("Error fetching bets:", error);
            return [];
        }
        return data || [];
    },

    async placeBet(matchId: string, selectionId: string, amount: number, odds: number, _possibleProfit: number) {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error("Not logged in");

        const { error } = await supabase
            .from('user_bets')
            .insert({
                user_id: user.id,
                match_id: matchId,
                selection_id: selectionId,
                amount: amount,
                odds: odds,
                profit: 0, // Pending outcome
                status: 'pending'
            });

        if (error) throw error;
    },

    // -- VALUE BETTING ENGINE (MOCK for Phase 2) -- //
    async getValueBets() {
        // In production, this would query the 'value_bets' table populated by metrics/value.py
        // For MVP, we simulate the output to match the Python engine
        const matches = await this.getMatchesToday();
        return matches
            .filter(() => Math.random() > 0.8) // Only top 20% are value
            .slice(0, 3) // Top 3 Daily Edge
            .map(m => ({
                match: m,
                bookmaker: "Pinnacle",
                notes: "Discrepancy in Clay Court surface ELO vs Market Odds.",
                wager_type: "WIN",
                selection: m.winner_name || m.player_a.name,
                odds: (1.8 + Math.random() * 1.5).toFixed(2),
                ev: (Math.random() * 15 + 5).toFixed(1), // 5% to 20% EV (High Quality)
                confidence: (75 + Math.random() * 15).toFixed(1), // 75-90% Conf
                kelly_stake: (Math.random() * 3 + 1).toFixed(1) // 1-4% Stake
            }));
    },

    async getValueAlerts() {
        try {
            const res = await fetch(`${this.baseUrl}/alerts/value`, {
                headers: await this.getHeaders()
            });
            // If 402/403, we return empty or special error to show Paywall
            if (res.status === 402 || res.status === 403) return "PREMIUM_REQUIRED";
            if (!res.ok) throw new Error("Alerts failed");
            return await res.json();
        } catch (e) {
            console.error("Alerts Error:", e);
            return [];
        }
    }
};
