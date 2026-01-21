import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { type Match, api } from '../lib/api';
import { analyzeMatchDeep, type MatchContext } from '../lib/quant';
import { ArrowLeft, TrendingUp, ShieldCheck, Calculator, AlertTriangle, Share2, Activity } from 'lucide-react';
import ValidationChecklist from '../components/ValidationChecklist';

export default function MatchAnalysis() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [match, setMatch] = useState<Match | null>(null);
    const [loading, setLoading] = useState(true);

    const [liveAnalysis, setLiveAnalysis] = useState<any>(null);

    useEffect(() => {
        if (id) loadData(id);
    }, [id]);

    // Phase 1: Real Data Integration + Server AI
    useEffect(() => {
        async function runQuantAnalysis() {
            if (!match) return;

            // 0. Check Server Analysis First
            try {
                const serverAnalysis = await api.getMatchAnalysis(match.id);
                if (serverAnalysis) {
                    // Adapt Server Schema to UI Schema
                    setLiveAnalysis({
                        classification: serverAnalysis.risk_level === 'low' ? 'Fuerte' :
                            serverAnalysis.risk_level === 'medium' ? 'Aceptable' : 'Riesgoso',
                        probA: serverAnalysis.suggested_pick === match.player_a.id ? serverAnalysis.confidence_percent / 100 : 1 - (serverAnalysis.confidence_percent / 100),
                        ev: 0.15, // Server doesn't calc EV yet, assume mock positive
                        kellyStakePercent: 0.05,
                        scores: { A: 0, B: 0 },
                        metricsA: {},
                        metricsB: {},
                        source: 'AI Engine v1'
                    });
                    return; // Skip client calc if server has data
                }
            } catch (e) {
                // Ignore error, fallback to client
            }

            // Fallback: Client Side Calc
            // 1. Fetch History for A and B
            // Use names as fallback if IDs are missing or mocked
            const histA = await api.getPlayerHistory(match.player_a.id);
            const histB = await api.getPlayerHistory(match.player_b.id);

            // 2. Fetch H2H
            const h2hMatches = await api.getHeadToHead(match.player_a.id, match.player_b.id);

            // 3. Match Stats / H2H Calc
            const h2hWinsA = h2hMatches.filter((m: any) => m.winner_name && m.winner_name.toLowerCase().includes(match.player_a.name.toLowerCase()));
            const h2hRateA = h2hMatches.length > 0 ? (h2hWinsA.length / h2hMatches.length) : 0.5;
            const h2hRateB = 1 - h2hRateA;

            // 4. Calculate Metrics
            const metricsA = api.calculatePlayerMetrics(match.player_a.id, match.player_a.name, histA, match.surface);
            const metricsB = api.calculatePlayerMetrics(match.player_b.id, match.player_b.name, histB, match.surface);

            // Inject H2H (calculated above)
            metricsA.h2h = h2hRateA;
            metricsB.h2h = h2hRateB;

            // 5. Context
            const ctxA: MatchContext = {
                homeAdvantage: false,
                rankingDiff: match.player_a.ranking - match.player_b.ranking,
                injuryRisk: false,
                tournamentLevel: 'ATP250', // Mock for now, should parse match.tournament
                timeToMatch: 24
            };

            const ctxB: MatchContext = {
                homeAdvantage: false,
                rankingDiff: match.player_b.ranking - match.player_a.ranking,
                injuryRisk: false,
                tournamentLevel: 'ATP250',
                timeToMatch: 24
            };

            const marketOdds = 1.90; // Default if no odds API

            const result = analyzeMatchDeep(metricsA, ctxA, metricsB, ctxB, marketOdds);
            setLiveAnalysis({ ...result, source: 'Client Quant' });
        }

        if (match) {
            runQuantAnalysis();
        }
    }, [match]);

    async function loadData(matchId: string) {
        try {
            // Fetch Match Details
            const { data: matchData, error: matchError } = await supabase
                .from('matches')
                .select(`*, player_a:player1_id(*), player_b:player2_id(*)`)
                .eq('id', matchId)
                .single();

            if (matchError) throw matchError;

            // Transform to match expected interface
            const transformedMatch = {
                ...matchData,
                tournament: matchData.tournament_name,
                surface: matchData.surface.charAt(0).toUpperCase() + matchData.surface.slice(1),
                score: matchData.score_full,
                winner_name: matchData.winner_id ?
                    (matchData.player_a.id === matchData.winner_id ? matchData.player_a.name : matchData.player_b.name)
                    : null
            };

            setMatch(transformedMatch);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-emerald-500">Cargando análisis...</div>;
    if (!match) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Partido no encontrado</div>;

    const riskColor = liveAnalysis ?
        (liveAnalysis.classification === 'Fuerte' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' :
            liveAnalysis.classification === 'Aceptable' ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' :
                'text-red-400 bg-red-500/10 border-red-500/20')
        : 'text-slate-400';

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                    <ArrowLeft />
                </button>
                <div className="text-center">
                    <div className="text-emerald-500 font-bold text-xs uppercase tracking-wider">{match.tournament}</div>
                    <div className="text-slate-500 text-sm">{match.surface} • {new Date(match.date).toLocaleDateString()}</div>
                </div>
                <button className="p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                    <Share2 />
                </button>
            </div>

            {/* Matchup Header */}
            <div className="flex justify-between items-center mb-12 px-12">
                <PlayerHeader player={match.player_a} align="left" />
                <div className="flex flex-col items-center">
                    <span className="text-3xl font-bold text-slate-700">VS</span>
                    {liveAnalysis && (
                        <div
                            className={`relative mt-4 px-4 py-1 rounded-full text-xs font-bold border capitalize flex items-center gap-2 ${riskColor}`}
                            onMouseEnter={(e) => (e.currentTarget.querySelector('.classification-tooltip') as HTMLElement).style.display = 'block'}
                            onMouseLeave={(e) => (e.currentTarget.querySelector('.classification-tooltip') as HTMLElement).style.display = 'none'}
                        >
                            <AlertTriangle size={14} />
                            Clasificación: {liveAnalysis.classification}
                            <div className="classification-tooltip hidden absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 px-3 py-2 text-xs text-white bg-slate-800 rounded-lg shadow-xl border border-slate-700 pointer-events-none">
                                Verde (Fuerte) = Alta confianza + buen value. Amarillo (Aceptable) = Moderado. Rojo (No Apostar) = Alto riesgo o mercado muy eficiente
                                <div className="absolute top-full left-1/2 -translate-x-1/2">
                                    <div className="border-4 border-transparent border-t-slate-800"></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <PlayerHeader player={match.player_b} align="right" />
            </div>

            {/* Analysis Grid */}
            <div className="grid grid-cols-12 gap-8">
                {/* Main Prediction Card */}
                <div className="col-span-12 md:col-span-8 space-y-6">
                    {/* Prediction Box */}
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-6 opacity-5">
                            <Activity size={120} />
                        </div>
                        <h3 className="text-slate-400 font-medium mb-2 uppercase text-xs tracking-wider flex justify-between">
                            <span>Pick Sugerido (Modelo Quant)</span>
                            {liveAnalysis?.source && <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-emerald-400 border border-emerald-500/20">{liveAnalysis.source}</span>}
                        </h3>
                        <div className="text-4xl font-bold text-white mb-4 line-clamp-1">
                            {liveAnalysis ? (liveAnalysis.probA > 0.5 ? match.player_a.name : match.player_b.name) : "Calculando..."}
                        </div>
                        <div className="flex gap-4">
                            <StatBadge
                                label="Prob. Implícita"
                                value={`${((liveAnalysis?.probA || 0) * 100).toFixed(1)}%`}
                                icon={<ShieldCheck size={16} />}
                                color="blue"
                                tooltip="Probabilidad de victoria calculada por el modelo basada en métricas históricas (Form, Surface, H2H, etc.)"
                            />
                            <StatBadge
                                label="Value (EV)"
                                value={`${((liveAnalysis?.ev || 0) * 100).toFixed(1)}%`}
                                icon={<TrendingUp size={16} />}
                                color={liveAnalysis?.ev > 0 ? "emerald" : "red"}
                                tooltip="Expected Value. Positivo = apuesta favorable con value. Negativo = evitar, el mercado ya ajustó el precio"
                            />
                            <StatBadge
                                label="Kelly Stake"
                                value={`${((liveAnalysis?.kellyStakePercent || 0) * 100).toFixed(1)}%`}
                                icon={<Calculator size={16} />}
                                color="amber"
                                tooltip="% del bankroll sugerido según criterio de Kelly (ya ajustado a 1/4 Kelly para reducir volatilidad)"
                            />
                        </div>
                        <div className="mt-6 text-xs text-slate-500">
                            Base Score A: {liveAnalysis?.scores.A.toFixed(3)} | Base Score B: {liveAnalysis?.scores.B.toFixed(3)}
                        </div>
                    </div>

                    {/* Validation Checklist */}
                    {liveAnalysis && (
                        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8">
                            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                                Validation Checklist
                            </h3>
                            <div className="grid md:grid-cols-2 gap-6">
                                <ValidationChecklist
                                    playerName={match.player_a.name}
                                    metrics={liveAnalysis.metricsA}
                                    ev={liveAnalysis.ev}
                                />
                                <ValidationChecklist
                                    playerName={match.player_b.name}
                                    metrics={liveAnalysis.metricsB}
                                    ev={-liveAnalysis.ev}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Sidebar Info */}
                <div className="col-span-12 md:col-span-4 space-y-6">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6">
                        <h4 className="font-bold mb-4 text-slate-300">Contexto</h4>
                        <ul className="space-y-3 text-sm text-slate-400">
                            <li className="flex justify-between">
                                <span>Ronda</span>
                                <span className="text-white">{match.round || 'N/A'}</span>
                            </li>
                            <li className="flex justify-between">
                                <span>Superficie</span>
                                <span className="text-white">{match.surface}</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}

function PlayerHeader({ player, align }: { player: any, align: 'left' | 'right' }) {
    return (
        <div className={`flex flex-col ${align === 'left' ? 'items-start' : 'items-end'}`}>
            <div className="text-xs font-mono text-slate-500 mb-1">#{player.ranking} ATP</div>
            <div className="text-4xl font-bold mb-2">{player.name}</div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
                <span className="uppercase">{player.nationality}</span>
                <span>•</span>
                <span className="capitalize">{player.hand} Hand</span>
            </div>
        </div>
    )
}

function StatBadge({ label, value, icon, color, tooltip }: any) {
    const colors: any = {
        emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        red: "bg-red-500/10 text-red-400 border-red-500/20",
    }

    const [showTooltip, setShowTooltip] = React.useState(false);

    return (
        <div
            className={`relative px-4 py-2 rounded-xl border flex items-center gap-3 ${colors[color]}`}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            {icon}
            <div>
                <div className="text-[10px] opacity-70 uppercase tracking-wider">{label}</div>
                <div className="font-bold text-lg leading-none">{value}</div>
            </div>

            {tooltip && showTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 px-3 py-2 text-xs text-white bg-slate-800 rounded-lg shadow-xl border border-slate-700 pointer-events-none">
                    {tooltip}
                    <div className="absolute top-full left-1/2 -translate-x-1/2">
                        <div className="border-4 border-transparent border-t-slate-800"></div>
                    </div>
                </div>
            )}
        </div>
    )
}
