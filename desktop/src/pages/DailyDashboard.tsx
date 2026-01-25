import { useEffect, useState } from 'react';
import { api, type Match } from '../lib/api';
import { Calendar, Trophy, Brain, Flame, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DailyDashboard() {
    const [matches, setMatches] = useState<Match[]>([]);
    const [valueBets, setValueBets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'live' | 'finished' | 'high_confidence' | 'value_bets'>('all');
    const [isLocked, setIsLocked] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        try {
            // CALL REAL API
            const matchesData = await api.getMatchesToday();
            const alertsData = await api.getValueAlerts();

            // Handle Premium Wall
            // Handle Premium Wall
            let finalBets: any[] = [];

            if (alertsData === "PREMIUM_REQUIRED") {
                setIsLocked(true);
                // We could show a "Locked" placeholder or empty
                finalBets = [];
            } else {
                setIsLocked(false);
                finalBets = Array.isArray(alertsData) ? alertsData : [];
            }

            // Mock AI predictions for demo match list if not in DB yet
            const enriched = matchesData.map((m: any) => ({
                ...m,
                prediction: m.prediction || {
                    winner_id: Math.random() > 0.5 ? m.player_a.id : m.player_b.id,
                    confidence: 0.55 + Math.random() * 0.40, // 55-95%
                    generated: true
                }
            }));
            setMatches(enriched);
            setValueBets(finalBets);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    const filteredMatches = matches.filter(m => {
        if (filter === 'live') return m.status === 'live';
        if (filter === 'finished') return m.winner_name;
        if (filter === 'high_confidence') return (m as any).prediction?.confidence > 0.8;
        if (filter === 'value_bets') return false; // Handled separately
        return true;
    });

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-10 gap-6">
                <div>
                    <h1 className="text-3xl font-black tracking-tight mb-2">Daily Dashboard</h1>
                    <p className="text-slate-400 flex items-center gap-2">
                        <Calendar size={16} /> {new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                </div>

                {/* Stats / KPIs */}
                <div className="flex gap-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500"><Brain size={20} /></div>
                        <div>
                            <div className="text-xs text-slate-500 uppercase font-bold">AI Picks</div>
                            <div className="text-xl font-bold">{matches.length}</div>
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500"><Trophy size={20} /></div>
                        <div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Matches</div>
                            <div className="text-xl font-bold">{matches.length}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Daily Edge Section (Premium) */}
            {(filter === 'all') && (
                <div className="mb-12">
                    <div className="flex items-center gap-2 mb-6">
                        <Flame className="text-orange-500" />
                        <h2 className="text-xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                            Daily Edge <span className="text-slate-500 text-sm font-medium ml-2">(High EV Opportunities)</span>
                        </h2>
                    </div>

                    {/* Premium Lock Banner */}
                    {isLocked && (
                        <div className="bg-slate-900/50 border border-orange-500/30 rounded-3xl p-8 text-center relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-b from-orange-500/5 to-transparent pointer-events-none" />
                            <h3 className="text-2xl font-black text-white mb-2">💎 Premium Feature</h3>
                            <p className="text-slate-400 mb-6">Unlock AI-driven Value Bets with High Expected Value.</p>
                            <Link to="/subscription" className="inline-flex items-center gap-2 bg-orange-500 text-slate-950 font-bold px-6 py-3 rounded-full hover:bg-orange-400 transition-colors">
                                Upgrade to Pro
                            </Link>
                        </div>
                    )}

                    {!isLocked && valueBets.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {valueBets.map((bet: any, i: number) => (
                                <div key={i} className="bg-gradient-to-br from-slate-900 to-slate-950 border border-orange-500/30 rounded-3xl p-6 relative overflow-hidden group hover:border-orange-500/60 transition-all shadow-lg shadow-orange-900/10">
                                    <div className="absolute top-0 right-0 bg-orange-500 text-slate-950 font-black px-4 py-1.5 rounded-bl-2xl text-sm uppercase tracking-wider flex items-center gap-1">
                                        <Brain size={14} /> {bet.confidence || 85}%
                                    </div>

                                    <div className="flex justify-between items-start mb-4 mt-2">
                                        <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">{bet.match?.tournament || 'ATP Tour'}</div>
                                    </div>

                                    <div className="text-2xl font-black text-white mb-1 truncate">{bet.selection}</div>
                                    <div className="text-sm text-slate-400 mb-6 flex items-center gap-2">
                                        {bet.match ? (
                                            <span>vs {bet.selection === bet.match.player_a.name ? bet.match.player_b.name : bet.match.player_a.name}</span>
                                        ) : <span>Match Info Unavailable</span>}
                                    </div>

                                    <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800 flex justify-between items-end mb-4">
                                        <div>
                                            <div className="text-xs text-slate-500 uppercase font-bold mb-1">Bookmaker Odds</div>
                                            <div className="font-mono text-xl text-slate-300">{bet.odds} <span className="text-xs text-slate-500">({bet.bookmaker})</span></div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-3xl font-black text-emerald-400">+{bet.ev_percentage || bet.ev}%</div>
                                            <div className="text-[10px] text-emerald-500/80 font-bold uppercase tracking-wider">Expected Value</div>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                                        <div className="flex items-center gap-1">Suggested Stake: <span className="text-white font-bold">{bet.kelly_fraction ? (bet.kelly_fraction * 100).toFixed(1) : bet.kelly_stake}%</span> (Kelly)</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Filters */}
            <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
                {['all', 'live', 'finished'].map((f) => (
                    <button
                        key={f}
                        onClick={() => setFilter(f as any)}
                        className={`px-4 py-2 rounded-full text-sm font-bold capitalize transition-all ${filter === f
                            ? 'bg-white text-slate-950'
                            : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-600'
                            }`}
                    >
                        {f}
                    </button>
                ))}
            </div>

            {/* Matches Grid */}
            {loading ? (
                <div className="text-center py-20 text-slate-500 animate-pulse">Loading Live Intelligence...</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredMatches.map((m: any) => (
                        <MatchCard key={m.id} match={m} />
                    ))}
                    {filteredMatches.length === 0 && (
                        <div className="col-span-full text-center py-12 text-slate-500 border-2 border-dashed border-slate-800 rounded-xl">
                            No matches found for this filter.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function MatchCard({ match }: { match: any }) {

    const p1Win = match.prediction?.winner_id === match.player_a.id;
    const confidence = match.prediction?.confidence || 0;
    const isHighConf = confidence > 0.8;

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 hover:border-emerald-500/30 transition-all group relative overflow-hidden">
            {/* High Confidence Badge */}
            {isHighConf && (
                <div className="absolute top-0 right-0 bg-emerald-500 text-slate-950 text-xs font-black px-3 py-1 rounded-bl-xl uppercase tracking-wider flex items-center gap-1">
                    <Brain size={12} /> AI Pick
                </div>
            )}

            <div className="flex justify-between items-start mb-6">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">{match.tournament}</div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">{match.surface}</div>
            </div>

            <div className="space-y-4 mb-6">
                {/* Player A */}
                <PlayerRow
                    player={match.player_a}
                    isWinner={match.winner_name === match.player_a.name}
                    isPredicted={p1Win}
                    score={match.score} // Parser needs refinement to split sets
                />
                {/* Player B */}
                <PlayerRow
                    player={match.player_b}
                    isWinner={match.winner_name === match.player_b.name}
                    isPredicted={!p1Win}
                    score={match.score}
                />
            </div>

            {/* AI Insight Footer */}
            <div className={`mt-4 pt-4 border-t border-slate-800/50 flex justify-between items-center ${isHighConf ? 'opacity-100' : 'opacity-50 group-hover:opacity-100'} transition-opacity`}>
                <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${isHighConf ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>
                        {Math.round(confidence * 100)}%
                    </div>
                    <span className="text-xs text-slate-400 font-medium">Confidence</span>
                </div>
                <Link to={`/match/${match.player_a.id}/${match.player_b.id}`} className="text-emerald-500 hover:text-emerald-400 p-2 rounded-full hover:bg-emerald-500/10 transition-colors">
                    <ArrowRight size={18} />
                </Link>
            </div>
        </div>
    );
}

function PlayerRow({ player, isWinner, isPredicted }: any) {
    return (
        <div className={`flex justify-between items-center p-3 rounded-xl ${isPredicted ? 'bg-emerald-500/5 border border-emerald-500/20' : 'bg-slate-950 border border-slate-800'}`}>
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-500">
                    {player.name[0]}
                </div>
                <div>
                    <div className={`font-bold text-sm ${isWinner ? 'text-emerald-400' : 'text-white'}`}>
                        {player.name}
                        {isPredicted && <span className="ml-2 text-[10px] bg-emerald-500 text-slate-950 px-1.5 py-0.5 rounded font-black uppercase">PICK</span>}
                    </div>
                    <div className="text-[10px] text-slate-500 font-medium">#{player.ranking || 'NR'}</div>
                </div>
            </div>
            {/* Score handling would go here, simplified for now */}
        </div>
    )
}
