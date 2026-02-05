import { useEffect, useState } from 'react';
import { api, type Match } from '../lib/api';
import { Calendar, Trophy, Brain, Flame, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DailyDashboard() {
    const [matches, setMatches] = useState<Match[]>([]);
    const [valueBets, setValueBets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'live' | 'finished' | 'high_confidence' | 'value_bets'>('all');
    const [selectedTournament, setSelectedTournament] = useState<string>('');
    const [isLocked, setIsLocked] = useState(false);
    const [debugError, setDebugError] = useState('');
    const [currentDate, setCurrentDate] = useState(new Date());

    useEffect(() => {
        loadData(currentDate);
    }, [currentDate]);

    async function loadData(dateObj: Date) {
        setLoading(true);
        try {
            // Force "YYYY-MM-DD" based on Local Time
            // This ensures that "Feb 4th" on the dashboard queries for "2026-02-04"
            const offset = dateObj.getTimezoneOffset();
            const localDate = new Date(dateObj.getTime() - (offset * 60 * 1000));
            const dateStr = localDate.toISOString().split('T')[0];

            console.log(`Fetching matches for ${dateStr}...`);
            const matchesData = await api.getMatchesByDate(dateStr);
            console.log("Matches:", matchesData);
            setMatches(matchesData);

            if (matchesData.length === 0) {
                // Clean UI for "0 matches", don't show red error box unless it's a code error
                setDebugError("");
            } else {
                setDebugError("");
            }

            const alertsData: any = await api.getValueAlerts();

            // Handle Premium Wall
            let finalBets: any[] = [];
            if (alertsData === "PREMIUM_REQUIRED") {
                setIsLocked(true);
                finalBets = [];
            } else {
                setIsLocked(false);
                finalBets = Array.isArray(alertsData) ? alertsData : [];
            }
            setValueBets(finalBets);
        } catch (e: any) {
            console.error(e);
            setDebugError("Error fetching: " + (e.message || JSON.stringify(e)));
        } finally {
            setLoading(false);
        }
    }

    const filteredMatches = matches.filter(m => {
        if (selectedTournament && m.tournament !== selectedTournament) return false;
        if (filter === 'live') return m.status === 'live';
        if (filter === 'finished') return m.winner_name || m.status === 'finished';
        if (filter === 'high_confidence') return (m as any).prediction?.confidence > 0.8;
        if (filter === 'value_bets') return false;
        return true;
    });

    // Get unique tournaments for filter dropdown
    const availableTournaments = Array.from(new Set(matches.map(m => m.tournament || 'Unknown Tournament'))).sort();

    // Priority Helper
    const getTournamentCode = (t: string) => {
        if (!t) return 7;
        const up = t.toUpperCase();
        if (up.includes('GRAND SLAM') || up.includes('OPEN')) return 1; // Highest
        if (up.includes('MASTER') || up.includes('1000')) return 2;
        if (up.includes('500')) return 3;
        if (up.includes('250')) return 4;
        if (up.includes('CHALLENGER')) return 5;
        if (up.includes('ITF')) return 6;
        return 7;
    };

    // Grouping Logic
    const getCategory = (m: Match) => {
        const t = (m.tournament || '').toUpperCase();
        if (t.includes('WTA') || t.includes('WOMEN')) return 'WTA';
        if (t.includes('ATP') || t.includes('MEN')) return 'ATP';
        if (t.includes('CHALLENGER')) return 'CHALLENGER';
        return 'ITF / OTHER';
    };

    const groupedMatches = filteredMatches.reduce((acc, match) => {
        const cat = getCategory(match);
        if (!acc[cat]) acc[cat] = {};

        const tourn = match.tournament || 'Unknown Tournament';
        if (!acc[cat][tourn]) acc[cat][tourn] = [];

        acc[cat][tourn].push(match);
        return acc;
    }, {} as Record<string, Record<string, Match[]>>);

    // Sort categories order
    const categoryOrder = ['ATP', 'WTA', 'CHALLENGER', 'ITF / OTHER'];

    const changeDate = (days: number) => {
        const newDate = new Date(currentDate);
        newDate.setDate(newDate.getDate() + days);
        setCurrentDate(newDate);
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white p-6 md:p-8">
            {/* Header / Week Calendar Strip */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-6">
                <div>
                    <h1 className="text-3xl font-black tracking-tight mb-4 flex items-center gap-2">
                        <Calendar className="text-emerald-500" />
                        Tennis Intelligence
                    </h1>

                    {/* Date Navigator */}
                    <div className="flex items-center gap-2 bg-slate-900 p-2 rounded-2xl border border-slate-800">
                        <button onClick={() => changeDate(-1)} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                            <ArrowRight className="rotate-180" size={20} />
                        </button>
                        <div className="flex flex-col items-center px-4 min-w-[140px]">
                            <span className="text-emerald-500 font-bold uppercase text-xs tracking-widest">
                                {currentDate.toDateString() === new Date().toDateString() ? 'TODAY' : currentDate.toLocaleDateString([], { weekday: 'short' })}
                            </span>
                            <span className="text-xl font-bold font-mono">
                                {currentDate.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                            </span>
                        </div>
                        <button onClick={() => changeDate(1)} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                            <ArrowRight size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex gap-4">
                    <button
                        onClick={() => loadData(currentDate)}
                        disabled={loading}
                        className={`p-3 rounded-full border border-slate-700 bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-all ${loading ? 'animate-spin opacity-50' : ''}`}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /><path d="M3 21v-5h5" /></svg>
                    </button>
                </div>
            </div>

            {/* Daily Edge Section (Only if Today or Future) */}
            {(filter === 'all' && currentDate >= new Date(new Date().setHours(0, 0, 0, 0))) && (
                <div className="mb-12">
                    <div className="flex items-center gap-2 mb-6 cursor-pointer" onClick={() => setFilter('value_bets')}>
                        <Flame className="text-orange-500" />
                        <h2 className="text-xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                            Daily Edge <span className="text-slate-500 text-sm font-medium ml-2">(High EV)</span>
                        </h2>
                    </div>

                    {/* Premium/Lock State */}
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

                    {/* Value Bets Grid */}
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
                                            <div className="text--[10px] text-emerald-500/80 font-bold uppercase tracking-wider">Expected Value</div>
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
            <div className="flex flex-col md:flex-row gap-4 mb-8">
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
                    {['all', 'live', 'finished'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f as any)}
                            className={`px-4 py-2 rounded-full text-sm font-bold capitalize transition-all whitespace-nowrap ${filter === f
                                ? 'bg-white text-slate-950'
                                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-600'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>

                {/* Tournament Filter Dropdown */}
                <div className="relative group min-w-[200px]">
                    <select
                        className="w-full bg-slate-900 text-white border border-slate-800 rounded-xl px-4 py-2 appearance-none focus:outline-none focus:border-emerald-500 cursor-pointer text-sm font-bold truncate pr-8"
                        onChange={(e) => setSelectedTournament(e.target.value)}
                        value={selectedTournament}
                    >
                        <option value="">All Tournaments ({matches.length})</option>
                        {availableTournaments.map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Matches Grid - GROUPED */}
            {/* Debug Info Panel - Temporary for Diagnosis */}


            {debugError && (
                <div className="bg-red-900/50 text-red-200 p-4 rounded mb-4 border border-red-500">
                    <p className="font-bold">⚠️ DEBUG INFO:</p>
                    <pre>{debugError}</pre>
                </div>
            )}

            {loading ? (
                <div className="text-center py-20 text-slate-500 animate-pulse">Fetching Tennis Intelligence...</div>
            ) : filteredMatches.length === 0 ? (
                <div className="col-span-full text-center py-12 text-slate-500 border-2 border-dashed border-slate-800 rounded-xl">
                    No matches found for {currentDate.toLocaleDateString()}.
                </div>
            ) : (
                <div className="space-y-12">
                    {categoryOrder.map(cat => {
                        const tournaments = groupedMatches[cat];
                        if (!tournaments) return null;

                        // Sort Tournaments by Priority
                        const sortedTournNames = Object.keys(tournaments).sort((a, b) => {
                            return getTournamentCode(a) - getTournamentCode(b);
                        });

                        return (
                            <div key={cat} className="animate-fade-in">
                                <div className="flex items-center gap-4 mb-6">
                                    <h2 className="text-4xl font-black text-slate-800 select-none">{cat}</h2>
                                    <div className="h-1 flex-1 bg-slate-900 rounded-full"></div>
                                </div>

                                <div className="space-y-8">
                                    {sortedTournNames.map((tournName) => {
                                        // Sort matches within tournament by TIME
                                        const matchesInTourn = tournaments[tournName].sort((a, b) =>
                                            new Date(a.date).getTime() - new Date(b.date).getTime()
                                        );

                                        return (
                                            <div key={tournName}>
                                                <h3 className="text-emerald-500 font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
                                                    <Trophy size={14} /> {tournName}
                                                </h3>
                                                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                                                    {matchesInTourn.map(m => (
                                                        <MatchCard key={m.id} match={m} />
                                                    ))}
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Footer */}
            <div className="mt-12 pt-8 border-t border-slate-800 text-center text-[10px] text-slate-600">
                <p>EDGESET Tennis Intelligence v2.0</p>
                <p>Automated Real-time Data</p>
            </div>
        </div>
    );
}

function MatchCard({ match }: { match: any }) {

    // 1. Prediction Data
    const p1Win = match.prediction?.winner_id === match.player_a.id;
    const confidence = match.prediction?.confidence || 0;
    const isHighConf = confidence > 0.75;
    const riskLevel = match.prediction?.risk_level || 'medium';

    // 2. Match Status & Result
    const isFinished = match.status === 'finished' || !!match.winner_name;
    const isLive = match.status === 'live';
    const showScore = isFinished || isLive;

    const winnerName = match.winner_name;
    const stats = match.stats_json;

    // Result Check logic
    let predictionResult: 'correct' | 'incorrect' | null = null;
    if (isFinished && match.prediction && winnerName) {
        const predictedSideName = match.prediction.winner_id === match.player_a.id ? match.player_a.name : match.player_b.name;
        // Loose string matching
        if (winnerName.toLowerCase().includes(predictedSideName.toLowerCase()) || predictedSideName.toLowerCase().includes(winnerName.toLowerCase())) {
            predictionResult = 'correct';
        } else {
            predictionResult = 'incorrect';
        }
    }

    // Risk Color Helper
    const getRiskColors = (level: string) => {
        if (level === 'low') return 'bg-emerald-500 text-slate-950 border-emerald-500';
        if (level === 'medium') return 'bg-amber-500 text-slate-950 border-amber-500';
        return 'bg-rose-500 text-white border-rose-500';
    };

    return (
        <div className={`
            bg-slate-900 border border-slate-800 rounded-3xl p-5 transition-all group relative overflow-hidden flex flex-col justify-between h-full
            ${isFinished ? 'hover:border-slate-600' : 'hover:border-emerald-500/30'}
        `}>
            {/* --- TOP HEADER: Tournament & Time --- */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">{match.tournament}</div>
                    <div className="flex items-center gap-2">
                        <div className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${match.surface === 'Hard' ? 'bg-blue-500/10 text-blue-400' : match.surface === 'Clay' ? 'bg-orange-500/10 text-orange-400' : 'bg-green-500/10 text-green-400'}`}>
                            {match.surface}
                        </div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                            {new Date(match.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                </div>

                {/* Status Badges */}
                {isFinished ? (
                    predictionResult ? (
                        <div className={`px-3 py-1 text-xs font-black uppercase tracking-wider rounded-lg flex items-center gap-1 border ${predictionResult === 'correct' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-red-500/10 text-red-500 border-red-500/20'
                            }`}>
                            {predictionResult === 'correct' ? '✅ AI HIT' : '❌ AI MISS'}
                        </div>
                    ) : (
                        <div className="px-3 py-1 bg-slate-800 text-slate-400 text-xs font-bold uppercase tracking-wider rounded-lg">
                            Finished
                        </div>
                    )
                ) : isLive ? (
                    <div className="px-3 py-1 bg-rose-500 text-white text-xs font-black uppercase tracking-wider rounded-lg animate-pulse shadow-[0_0_15px_-3px_rgba(244,63,94,0.6)]">
                        LIVE SCORE
                    </div>
                ) : (
                    // Scheduled / AI Status
                    isHighConf && (
                        <div className="px-3 py-1 bg-emerald-500 text-slate-950 text-xs font-black uppercase tracking-wider rounded-lg flex items-center gap-1 shadow-[0_0_15px_-3px_rgba(16,185,129,0.4)]">
                            <Brain size={12} /> AI PICK
                        </div>
                    )
                )}
            </div>

            {/* --- PLAYERS SECTION --- */}
            <div className="space-y-3 mb-6 flex-1">
                {/* Player A */}
                <PlayerRow
                    player={match.player_a}
                    isWinner={winnerName === match.player_a.name}
                    isPredicted={p1Win}
                    showScore={showScore} // Changed prop name for clarity
                    score={match.score}
                    winProb={match.prediction ? (p1Win ? confidence : 1 - confidence) : 0.5}
                />

                {/* VS Divider (styled) */}
                <div className="relative flex items-center justify-center my-2">
                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                        {!showScore && <div className="w-full border-t border-slate-800/50"></div>}
                    </div>
                    {!showScore && <span className="relative bg-slate-900 px-2 text-[10px] font-bold text-slate-600">VS</span>}
                </div>

                {/* Player B */}
                <PlayerRow
                    player={match.player_b}
                    isWinner={winnerName === match.player_b.name}
                    isPredicted={!p1Win} // If p1Win is false, and prediction exists, then p2 is predicted
                    showScore={showScore}
                    score={match.score}
                    winProb={match.prediction ? (!p1Win ? confidence : 1 - confidence) : 0.5}
                />
            </div>

            {/* --- METRICS / STATS FOOTER --- */}
            {isFinished && stats ? (
                // FINISHED: Show Stats (Aces, DF, BP)
                <div className="mt-4 pt-4 border-t border-slate-800/50 grid grid-cols-3 gap-2 text-center relative group-hover:opacity-100 transition-opacity">
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Aces</div>
                        <div className="text-sm font-bold text-slate-300">
                            <span className="text-emerald-500">{stats.p1_aces || '-'}</span> / <span className="text-blue-500">{stats.p2_aces || '-'}</span>
                        </div>
                    </div>
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Breaks</div>
                        <div className="text-sm font-bold text-slate-300">
                            {stats.p1_break_points_converted || '-'} / {stats.p2_break_points_converted || '-'}
                        </div>
                    </div>
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Points</div>
                        <div className="text-sm font-bold text-slate-300">
                            {stats.p1_total_points_won || '-'} / {stats.p2_total_points_won || '-'}
                        </div>
                    </div>
                </div>
            ) : match.prediction ? (
                // PREDICTION: Show AI Metrics (Prob, Risk, Model)
                <div className="mt-4 pt-4 border-t border-slate-800/50">
                    <div className="flex justify-between items-center mb-3">
                        <div className="flex items-center gap-2">
                            <div className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${getRiskColors(riskLevel)}`}>
                                {riskLevel} RISK
                            </div>
                            <div className="text-[10px] text-slate-500 font-medium">Model {match.prediction.model_version}</div>
                        </div>
                        <div className="text-right">
                            <div className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider">Win Prob</div>
                            <div className="text-lg font-black text-white leading-none">{(confidence * 100).toFixed(1)}%</div>
                        </div>
                    </div>
                    {/* Probability Bar */}
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
                        <div
                            className={`h-full ${p1Win ? 'bg-emerald-500' : 'bg-slate-700'} transition-all duration-1000`}
                            style={{ width: `${(p1Win ? confidence : 1 - confidence) * 100}%` }}
                        />
                        <div
                            className={`h-full ${!p1Win ? 'bg-blue-500' : 'bg-slate-700'} transition-all duration-1000`}
                            style={{ width: `${(!p1Win ? confidence : 1 - confidence) * 100}%` }}
                        />
                    </div>
                    <Link to={`/match/${match.player_a.id}/${match.player_b.id}`} className="mt-3 block w-full text-center py-2 rounded-xl bg-slate-800 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition-colors">
                        View Full Analysis
                    </Link>
                </div>
            ) : (
                // NO DATA
                <div className="mt-4 pt-4 border-t border-slate-800/50 text-center">
                    <span className="text-xs text-slate-500 italic">No AI Analysis available yet</span>
                </div>
            )}
        </div>
    );
}

function PlayerRow({ player, isWinner, isPredicted, showScore, score, winProb }: any) {
    return (
        <div className={`flex justify-between items-center p-3 rounded-xl transition-all ${isPredicted && !showScore ? 'bg-emerald-500/5 border border-emerald-500/20'
            : isWinner ? 'bg-gradient-to-r from-emerald-500/10 to-transparent border border-emerald-500/20'
                : 'bg-slate-950 border border-slate-800'
            }`}>
            <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border ${isWinner ? 'border-emerald-500 text-emerald-400 bg-emerald-500/10' : 'border-slate-700 bg-slate-800 text-slate-500'}`}>
                    {player.name[0]}
                </div>
                <div>
                    <div className="flex items-center gap-2">
                        <div className={`font-bold text-sm ${isWinner ? 'text-emerald-400' : 'text-slate-200'}`}>
                            {player.name}
                        </div>
                        {isPredicted && !showScore && <Brain size={12} className="text-emerald-500" />}
                        {isWinner && <Trophy size={12} className="text-emerald-500" />}
                    </div>
                    {!showScore && (
                        <div className="text-[10px] text-slate-500 font-medium flex items-center gap-2">
                            <span>#{player.ranking || 'NR'}</span>
                            <span className="text-slate-600">•</span>
                            <span className={`${winProb > 0.6 ? 'text-emerald-500' : 'text-slate-500'}`}>{(winProb * 100).toFixed(0)}% Win Prob</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Score Display (Simple) */}
            <div className="text-right">
                {showScore && score ? (
                    <div className={`font-mono font-bold text-sm ${isWinner ? 'text-white' : 'text-slate-400'}`}>
                        {score}
                    </div>
                ) : null}
            </div>
        </div>
    )
}
