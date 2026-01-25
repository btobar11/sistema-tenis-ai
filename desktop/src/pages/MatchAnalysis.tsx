import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { type Match, api } from '../lib/api';
import { analyzeMatch } from '../lib/quant';
import { ArrowLeft, TrendingUp, ShieldCheck, Calculator, Activity } from 'lucide-react';
import ValidationChecklist from '../components/ValidationChecklist';

interface MatchAnalysisProps {
    matchId?: string;
    onBack?: () => void;
}

export default function MatchAnalysis({ matchId, onBack }: MatchAnalysisProps = {}) {
    const { id } = useParams();
    const finalId = matchId || id;
    const navigate = useNavigate();
    const [match, setMatch] = useState<Match | null>(null);
    const [loading, setLoading] = useState(true);

    // State for Subscription
    const [isPremium, setIsPremium] = useState(false);

    useEffect(() => {
        checkSubscription();
    }, []);

    async function checkSubscription() {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            // UNLOCKED FOR DESKTOP CLIENT
            setIsPremium(true);
        }
    }

    useEffect(() => {
        if (finalId) {
            loadMatch(finalId);
        }
    }, [finalId]);

    async function loadMatch(matchId: string) {
        setLoading(true);
        try {
            const data = await api.getMatch(matchId);
            setMatch(data);
        } catch (e) {
            console.error(e);
            navigate('/');
        } finally {
            setLoading(false);
        }
    }

    const liveAnalysis = match ? analyzeMatch(match) : null;

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
            </div>
        );
    }

    if (!match) return null;

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            {/* Header */}
            <header className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => onBack ? onBack() : navigate('/')}
                    className="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400 hover:text-white"
                >
                    <ArrowLeft size={24} />
                </button>
                <div>
                    <h1 className="text-xl font-bold flex items-center gap-2">
                        <span>{match.tournament}</span>
                        <span className="text-slate-500 text-sm font-normal">| {match.round}</span>
                    </h1>
                    <div className="text-sm text-slate-400">
                        {new Date(match.date).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-12 gap-8">
                {/* Main Analysis Column */}
                <div className="col-span-12 md:col-span-8 space-y-6">

                    {/* Scoreboard */}
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8">
                        <div className="flex justify-between items-center mb-8">
                            <PlayerHeader player={match.player_a} align="left" />
                            <div className="text-2xl font-bold text-slate-700">VS</div>
                            <PlayerHeader player={match.player_b} align="right" />
                        </div>
                    </div>

                    {/* Prediction Box with Premium Gate */}
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 relative overflow-hidden">

                        {/* Premium Lock Overlay */}
                        {!isPremium && (
                            <div className="absolute inset-0 z-50 bg-slate-900/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                                <ShieldCheck className="w-16 h-16 text-emerald-500 mb-4" />
                                <h3 className="text-2xl font-bold text-white mb-2">Análisis Premium Bloqueado</h3>
                                <p className="text-slate-300 mb-6 max-w-md">
                                    La Inteligencia Artificial ha detectado una oportunidad de alto valor. Desbloquea este pick y accede al análisis completo.
                                </p>
                                <button className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg shadow-emerald-500/20 transform hover:scale-105">
                                    Desbloquear Premium ($29/mes)
                                </button>
                                <p className="mt-4 text-xs text-slate-500">Garantía de reembolso de 7 días.</p>
                            </div>
                        )}

                        <div className="absolute top-0 right-0 p-6 opacity-5">
                            <Activity size={120} />
                        </div>
                        <h3 className="text-slate-400 font-medium mb-2 uppercase text-xs tracking-wider flex justify-between">
                            <span>Pick Sugerido (Modelo Quant)</span>
                            {liveAnalysis?.source && <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-emerald-400 border border-emerald-500/20">{liveAnalysis.source}</span>}
                        </h3>
                        <div className="text-4xl font-bold text-white mb-4 line-clamp-1 blur-sm select-none">
                            {!isPremium ? "Hidden Pick ????" : (liveAnalysis ? (liveAnalysis.probA > 0.5 ? match?.player_a.name : match?.player_b.name) : "Calculando...")}
                        </div>
                        <div className="flex gap-4 opacity-50 pointer-events-none filter blur-sm">
                            <StatBadge
                                label="Prob. Implícita"
                                value="76.4%"
                                icon={<ShieldCheck size={16} />}
                                color="blue"
                            />
                            <StatBadge
                                label="Value (EV)"
                                value="+12.5%"
                                icon={<TrendingUp size={16} />}
                                color="emerald"
                            />
                            <StatBadge
                                label="Kelly Stake"
                                value="4.5%"
                                icon={<Calculator size={16} />}
                                color="amber"
                            />
                        </div>
                        {isPremium && (
                            <div className="mt-6 text-xs text-slate-500">
                                Base Score A: {liveAnalysis?.scores.A.toFixed(3)} | Base Score B: {liveAnalysis?.scores.B.toFixed(3)}
                            </div>
                        )}
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
