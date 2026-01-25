export interface PlayerMetrics {
    winrateSurface: number; // 0-1
    form: number;           // 0-1
    regularity: number;     // 0-1 (1 - stdDev)
    h2h: number;            // 0-1
    setTrend: number;       // 0-1
}

export interface MatchContext {
    homeAdvantage: boolean;
    rankingDiff: number; // Player Rank - Opponent Rank
    injuryRisk: boolean;
    tournamentLevel: 'GrandSlam' | 'Masters1000' | 'ATP500' | 'ATP250' | 'Challenger';
    timeToMatch: number; // Hours
}

// Weights defined by the user
const WEIGHTS = {
    w1: 0.25, // Winrate Surface
    w2: 0.20, // Form
    w3: 0.20, // Regularity
    w4: 0.10, // Set Trend
    w5: 0.15, // H2H
};

// -- 1. Basic Scoring Logic -- //

export function calculateBaseScore(metrics: PlayerMetrics): number {
    return (
        metrics.winrateSurface * WEIGHTS.w1 +
        metrics.form * WEIGHTS.w2 +
        metrics.regularity * WEIGHTS.w3 +
        metrics.setTrend * WEIGHTS.w4 +
        metrics.h2h * WEIGHTS.w5
    );
}

export function calculateContextFactor(ctx: MatchContext): number {
    const alpha = 0.04;
    const beta = 0.001;
    const rankingBonus = Math.abs(ctx.rankingDiff) * beta;
    const rankFactor = ctx.rankingDiff < 0 ? (1 + rankingBonus) : 1;
    const gamma = 0.20;

    let factor = 1;
    if (ctx.homeAdvantage) factor *= (1 + alpha);
    factor *= rankFactor;
    if (ctx.injuryRisk) factor *= (1 - gamma);

    return factor;
}

export function calculateFinalScore(metrics: PlayerMetrics, ctx: MatchContext): number {
    const base = calculateBaseScore(metrics);
    const factor = calculateContextFactor(ctx);
    return base * factor;
}

export function calculateWinProbability(scoreA: number, scoreB: number, k: number = 6.5): number {
    const delta = scoreA - scoreB;
    return 1 / (1 + Math.exp(-k * delta));
}

export function calculateEV(modelProb: number, odds: number): number {
    return (modelProb * odds) - 1;
}

// -- 2. Deep Quant: Real Edge & Market Efficiency -- //

export function estimateMarketEfficiency(tournamentLevel: string): number {
    // 1 - Avg(|CLV|)
    // Grand Slams are highly efficient (hard to beat). Challengers are inefficient.
    switch (tournamentLevel) {
        case 'GrandSlam': return 0.98;
        case 'Masters1000': return 0.95;
        case 'ATP500': return 0.92;
        case 'ATP250': return 0.90;
        case 'Challenger': return 0.85; // Sweet spot
        default: return 0.90;
    }
}

export function predictClosingLine(
    oddsOpen: number,
    steamProb: number, // 0-1, likelihood of steam
    efficiency: number
): number {
    // Simple heuristic model:
    // If inefficient market + steam likely -> Odds will drop significantly.
    // If efficient -> Odds verify close to Open.
    const expectedDrop = steamProb * (1 - efficiency) * 0.20; // Max 20% drop
    return oddsOpen * (1 - expectedDrop);
}

export function calculateTrueEdge(oddsOpen: number, predictedClosingOdds: number): number {
    if (predictedClosingOdds <= 1) return 0;
    return (oddsOpen / predictedClosingOdds) - 1;
}

// -- 3. Portfolio & Risk Management (Hedge Fund Level) -- //

export interface PortfolioConstraints {
    maxExposureTournament: number; // 0.15
    maxExposurePlayer: number; // 0.10
    maxDailyRisk: number; // 0.05
}

export function calculatePortfolioKellyStake(
    prob: number,
    odds: number,
    bankroll: number,
    correlationPenalty: number = 0
): number {
    // Kelly with correlation dampening
    // f = [(bp - q) / b] * (1 - correlation)
    if (odds <= 1) return 0;
    const f = (prob * odds - 1) / (odds - 1);
    if (f <= 0) return 0;

    const dampenedF = f * (1 - correlationPenalty);
    return dampenedF * bankroll * 0.25; // Quarter Kelly
}

// -- 4. Final Decision Engine -- //

export type BetClassification = 'Fuerte' | 'Aceptable' | 'No Apostar (Eficiencia)' | 'No Apostar (Riesgo)';

export function classifyBetDeepQuant(
    evObserved: number,
    trueEdge: number,
    efficiency: number,
    riskLevel: 'Low' | 'Medium' | 'High'
): BetClassification {

    // 1. Efficiency Gate
    if (efficiency > 0.96) return 'No Apostar (Eficiencia)'; // Market too tough (e.g. Nadal at Roland Garros final)

    // 2. Edge Gate
    if (trueEdge < 0) return 'No Apostar (Riesgo)'; // Negative Expected CLV

    // 3. Pro Rules
    if (evObserved >= 0.10 && trueEdge >= 0.05 && riskLevel !== 'High') return "Fuerte";
    if (evObserved >= 0.05 && riskLevel !== 'High') return "Aceptable";

    return 'No Apostar (Riesgo)';
}

// -- 5. Portfolio Monte Carlo -- //

export interface PortfolioSimResult {
    maxDrawdown: number;
    probRuin: number;
    cagr: number;
    sharpe: number;
}

export function runPortfolioMonteCarlo(
    avgWinRate: number,
    avgOdds: number,
    tradesPerDay: number,
    days: number = 1000 // Reduced for perf in JS
): PortfolioSimResult {
    // Simplified Simulation
    const initialBankroll = 1000;
    let bankroll = initialBankroll;
    let peak = initialBankroll;
    let maxDrawdown = 0;
    let ruins = 0;

    // Simulate 100 paths
    const paths = 20;
    let totalReturn = 0;

    for (let p = 0; p < paths; p++) {
        bankroll = initialBankroll;
        peak = initialBankroll;
        let localDrawdown = 0;

        for (let d = 0; d < days; d++) {
            for (let t = 0; t < tradesPerDay; t++) {
                // Fixed stake 2% for sim
                const stake = bankroll * 0.02;
                if (Math.random() < avgWinRate) {
                    bankroll += stake * (avgOdds - 1);
                } else {
                    bankroll -= stake;
                }
            }
            if (bankroll > peak) peak = bankroll;
            const dd = (peak - bankroll) / peak;
            if (dd > localDrawdown) localDrawdown = dd;

            if (bankroll <= 0) {
                break;
            }
        }

        if (bankroll <= 0) ruins++;
        if (localDrawdown > maxDrawdown) maxDrawdown = localDrawdown;
        totalReturn += (bankroll / initialBankroll);
    }

    return {
        maxDrawdown,
        probRuin: ruins / paths,
        cagr: (totalReturn / paths) - 1, // Simplified
        sharpe: 1.5 // Mock for prototype
    };
}

// Helper to get formatted analysis
export function analyzeMatchDeep(
    pA: PlayerMetrics, ctxA: MatchContext,
    pB: PlayerMetrics, ctxB: MatchContext,
    marketOddsA: number,
    marketOddsOpenA: number = marketOddsA
) {
    const scoreA = calculateFinalScore(pA, ctxA);
    const scoreB = calculateFinalScore(pB, ctxB);

    const probA = calculateWinProbability(scoreA, scoreB);

    // Basic EV
    const evRaw = calculateEV(probA, marketOddsA);

    // Deep Quant
    const efficiency = estimateMarketEfficiency(ctxA.tournamentLevel);
    const predictedClosing = predictClosingLine(marketOddsOpenA, 0.5, efficiency);
    const trueEdge = calculateTrueEdge(marketOddsOpenA, predictedClosing);

    // Risk Level Inference
    const deltaConfidence = Math.abs(probA - 0.5);
    const riskLevel = deltaConfidence < 0.1 ? 'High' : deltaConfidence < 0.2 ? 'Medium' : 'Low';

    const decision = classifyBetDeepQuant(evRaw, trueEdge, efficiency, riskLevel);

    // Portfolio Sim (On the fly - usually precomputed)
    const sim = runPortfolioMonteCarlo(probA, marketOddsA, 3);

    return {
        scores: { A: scoreA, B: scoreB },
        probA,
        marketOdds: marketOddsA,
        predictedClosing,
        efficiency,
        trueEdge,
        ev: evRaw,
        classification: decision,
        portfolioSim: sim,
        kellyStakePercent: calculatePortfolioKellyStake(probA, marketOddsA, 100) / 100,
        metricsA: pA,
        metricsB: pB,
        source: 'Client-Quant v1'
    };
}

/**
 * Adapter to convert Match object (with optional stats_json) to PlayerMetrics
 * for the deep quant engine.
 */
import type { Match } from './api';

export function analyzeMatch(match: Match) {
    const stats = match.stats_json || {};

    // Default metrics if not present
    const defaultMetrics: PlayerMetrics = {
        winrateSurface: 0.5, form: 0.5, regularity: 0.5, h2h: 0.5, setTrend: 0.5
    };

    const pA: PlayerMetrics = stats.pA || defaultMetrics;
    const pB: PlayerMetrics = stats.pB || defaultMetrics;

    const ctxA: MatchContext = {
        homeAdvantage: false,
        rankingDiff: (match.player_b.ranking - match.player_a.ranking),
        injuryRisk: false,
        tournamentLevel: 'ATP250',
        timeToMatch: 24
    };

    const ctxB: MatchContext = { ...ctxA, rankingDiff: -ctxA.rankingDiff };

    return analyzeMatchDeep(pA, ctxA, pB, ctxB, 1.90);
}
