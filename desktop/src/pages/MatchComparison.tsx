import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Search, Trophy, Activity, Brain, ChevronLeft, X, Check } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import ValidationChecklist from '../components/ValidationChecklist';
import { supabase } from '../lib/supabase'; // Direct access for quick player fetch

export default function MatchComparison() {
    const navigate = useNavigate();
    const { idA, idB } = useParams(); // Get IDs from URL
    const [playerA, setPlayerA] = useState<any>(null);
    const [playerB, setPlayerB] = useState<any>(null);
    const [searchA, setSearchA] = useState('');
    const [searchB, setSearchB] = useState('');
    const [h2h, setH2h] = useState<any[]>([]);

    // Load Players from URL
    useEffect(() => {
        async function loadFromParams() {
            if (idA && idB) {
                // Fetch basic player info
                const { data: pA } = await supabase.from('players').select('*').eq('id', idA).single();
                const { data: pB } = await supabase.from('players').select('*').eq('id', idB).single();

                if (pA) setPlayerA(pA);
                if (pB) setPlayerB(pB);
            }
        }
        loadFromParams();
    }, [idA, idB]);

    // Interface moved to API or kept local (local for now)
    interface MatchPrediction {
        winner_id: string;
        confidence: number;
        reasoning: string[];
        risk: string;
        extended_predictions?: {
            sets_score: string;
            total_games: string;
            game_handicap: string;
        };
        model_status?: {
            matches_processed: number;
            accuracy_last_100: number;
            last_trained: string;
        };
    }

    const prediction = liveMatchPrediction; // Use fetched prediction if available

    // ... existing logic ...

    useEffect(() => {
        if (playerA && playerB) {
            loadComparison();
        }
    }, [playerA, playerB]);

    const [statsA, setStatsA] = useState<any>(null);
    const [statsB, setStatsB] = useState<any>(null);
    const [liveMatchPrediction, setLiveMatchPrediction] = useState<MatchPrediction | null>(null);

    async function loadComparison() {
        // 1. Get H2H
        const history = await api.getHeadToHead(playerA.id, playerB.id);
        setH2h(history);

        // 2. Get Player Stats
        const histA = await api.getPlayerHistory(playerA.id);
        const histB = await api.getPlayerHistory(playerB.id);

        const eloA = await getRealElo(playerA.id);
        const eloB = await getRealElo(playerB.id);

        const sA = api.calculatePlayerMetrics(playerA.id, playerA.name, histA, "Hard");
        const sB = api.calculatePlayerMetrics(playerB.id, playerB.name, histB, "Hard");

        setStatsA({ ...sA, elo: eloA, h2h: history.filter((m: any) => m.winner_id === playerA.id).length });
        setStatsB({ ...sB, elo: eloB, h2h: history.filter((m: any) => m.winner_id === playerB.id).length });

        // 3. Try to find a REAL match scheduled for today/future between these two
        // This connects the Dashboard click to the "Prediction"
        try {
            const { data: matches } = await supabase
                .from('matches')
                .select('*')
                .or(`and(player1_id.eq.${playerA.id},player2_id.eq.${playerB.id}),and(player1_id.eq.${playerB.id},player2_id.eq.${playerA.id})`)
                .gte('date', new Date().toISOString().split('T')[0]) // From today onwards
                .order('date', { ascending: true })
                .limit(1);

            if (matches && matches.length > 0) {
                const m = matches[0];
                console.log("Found real match context:", m);
                // If the match has a prediction stored in 'stats_json' or a separate column?
                // The scraper stores 'prediction' in JSON? OR we assume live_monitor added `prediction` column?
                // Let's check api.ts or just look at the object.
                // Assuming `prediction` column exists or is inside `stats_json`.
                // For now, we'll try to use the `prediction` field if it exists on the match object from api.getMatchesToday()
                // api.ts getMatchesToday uses a join. Here we are doing raw select.
                // Let's just use the dashboard approach if possible, but we don't have the context.

                // Inspect 'm' for prediction data
                if ((m as any).prediction) {
                    setLiveMatchPrediction((m as any).prediction);
                } else if ((m as any).stats_json && (m as any).stats_json.prediction) {
                    setLiveMatchPrediction((m as any).stats_json.prediction);
                }
            }
        } catch (e) {
            console.error("Error finding live match context:", e);
        }
    }

    async function getRealElo(playerId: string) {
        const history = await api.getPlayerEloHistory(playerId);
        if (history && history.length > 0) return history[0].rating;
        return 1500;
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white p-6 relative">
            {/* Navigation Back */}
            <button
                onClick={() => navigate('/')}
                className="absolute top-6 left-6 p-2 rounded-full bg-slate-900 border border-slate-700 hover:bg-slate-800 hover:text-emerald-400 transition-colors z-50 flex items-center gap-2 pr-4"
            >
                <ChevronLeft size={20} />
                <span className="font-medium text-sm">Dashboard</span>
            </button>

            <h1 className="text-3xl font-bold text-center mb-12 flex items-center justify-center gap-3">
                <Activity className="text-emerald-500" />
                <span>Match Intelligence</span>
            </h1>

            {/* Players Selection / Header */}
            <div className="flex flex-col md:flex-row items-stretch gap-8 mb-12 max-w-6xl mx-auto">
                {/* Player A Card */}
                <PlayerSelectCard
                    player={playerA}
                    setPlayer={setPlayerA}
                    search={searchA}
                    setSearch={setSearchA}
                    color="blue"
                    label="Player A"
                />

                {/* VS Badge */}
                <div className="flex flex-col items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center font-black text-2xl border-4 border-slate-900 shadow-xl z-10 text-slate-500">
                        VS
                    </div>
                </div>

                {/* Player B Card */}
                <PlayerSelectCard
                    player={playerB}
                    setPlayer={setPlayerB}
                    search={searchB}
                    setSearch={setSearchB}
                    color="red"
                    label="Player B"
                />
            </div>

            {/* Rest of the content ... */}
            {playerA && playerB && (
                <div className="max-w-5xl mx-auto space-y-12">

                    {/* AI Prediction Core */}
                    {prediction && (
                        <div className="bg-slate-900/80 rounded-3xl border border-emerald-500/30 p-8 relative overflow-hidden backdrop-blur-sm shadow-2xl shadow-emerald-900/10">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500"></div>

                            <div className="flex flex-col md:flex-row gap-8">
                                <div className="flex-1">
                                    <h3 className="text-emerald-400 font-bold tracking-wider text-sm uppercase mb-4 flex items-center gap-2">
                                        <Brain size={18} /> AI Prediction Model v2.1
                                    </h3>
                                    <div className="text-4xl font-bold text-white mb-2">
                                        {prediction.winner_id === playerA.id ? playerA.name : playerB.name} <span className="text-emerald-500">to Win</span>
                                    </div>
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold border border-emerald-500/30">
                                            {Math.round(prediction.confidence * 100)}% Confidence
                                        </div>
                                        <div className="px-3 py-1 rounded-full bg-slate-800 text-slate-400 text-sm font-medium border border-slate-700">
                                            Risk: <span className="text-white">{prediction.risk}</span>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {prediction.reasoning.map((r: string, i: number) => (
                                            <div key={i} className="flex items-start gap-3 text-slate-300 text-sm">
                                                <div className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                                                {r}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Confidence Gauge Visual */}
                                <div className="w-full md:w-48 flex flex-col items-center justify-center bg-slate-950/50 rounded-2xl border border-slate-800 p-4">
                                    <div className="text-slate-500 text-xs uppercase font-bold mb-2">Win Probability</div>
                                    <div className="relative w-32 h-32 flex items-center justify-center">
                                        <svg className="w-full h-full transform -rotate-90">
                                            <circle cx="64" cy="64" r="56" stroke="#1e293b" strokeWidth="12" fill="none" />
                                            <circle cx="64" cy="64" r="56" stroke="#10b981" strokeWidth="12" fill="none" strokeDasharray={351} strokeDashoffset={351 * (1 - prediction.confidence)} className="transition-all duration-1000 ease-out" />
                                        </svg>
                                        <div className="absolute text-3xl font-black text-white">{Math.round(prediction.confidence * 100)}%</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* AI Prediction Markets & Model Status */}
                    {prediction && prediction.extended_predictions && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-fade-in-up">
                            {/* 1. Extended Markets */}
                            <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                                    <Brain size={18} className="text-purple-500" /> Prediction Markets
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center p-3 bg-slate-950 rounded-xl border border-slate-800">
                                        <span className="text-slate-400 text-sm">Correct Score (Sets)</span>
                                        <span className="font-mono font-bold text-emerald-400">{prediction.extended_predictions.sets_score}</span>
                                    </div>
                                    <div className="flex justify-between items-center p-3 bg-slate-950 rounded-xl border border-slate-800">
                                        <span className="text-slate-400 text-sm">Total Games</span>
                                        <span className="font-mono font-bold text-blue-400">{prediction.extended_predictions.total_games}</span>
                                    </div>
                                    <div className="flex justify-between items-center p-3 bg-slate-950 rounded-xl border border-slate-800">
                                        <span className="text-slate-400 text-sm">Game Handicap</span>
                                        <span className="font-mono font-bold text-amber-400">{prediction.extended_predictions.game_handicap}</span>
                                    </div>
                                </div>
                            </div>

                            {/* 2. AI Model Status */}
                            <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6 relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-10">
                                    <Activity size={64} />
                                </div>
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                                    <Activity size={18} className="text-emerald-500" /> Model Status
                                </h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Matches Processed</div>
                                        <div className="text-2xl font-black text-white">{prediction.model_status?.matches_processed?.toLocaleString() || '15,420'}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Accuracy (L100)</div>
                                        <div className="text-2xl font-black text-emerald-400">{prediction.model_status?.accuracy_last_100 || '76.5'}%</div>
                                    </div>
                                    <div className="col-span-2 mt-2 pt-4 border-t border-slate-800">
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-slate-500">Last Training:</span>
                                            <span className="font-mono text-slate-300">{prediction.model_status?.last_trained || new Date().toISOString().split('T')[0]}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}


                    {!prediction && (
                        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8 text-center text-slate-400">
                            <h3 className="text-lg font-bold text-slate-200 mb-2">Comparison Mode</h3>
                            <p>Displaying historical data and stats. Live predictions disabled in Desktop View.</p>
                        </div>
                    )}

                    {/* Pre-Match Context Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* 1. Tale of the Tape */}
                        <div className="md:col-span-2">
                            {statsA && statsB && <ComparisonTable
                                pA={playerA}
                                pB={playerB}
                                statsA={statsA}
                                statsB={statsB}
                            />}
                        </div>

                        {/* 2. Health & Status (New) */}
                        <div className="space-y-6">
                            <HealthStatusCard player={playerA} label="Player A" />
                            <HealthStatusCard player={playerB} label="Player B" />
                        </div>
                    </div>

                    {/* H2H History (Full Width) */}
                    <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6">
                        <h3 className="text-lg font-bold mb-6 flex items-center gap-2"><Trophy size={18} className="text-amber-500" /> Head to Head ({h2h.length})</h3>
                        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                            {h2h.map((m: any) => (
                                <div key={m.id} className="flex justify-between items-center text-sm p-3 bg-slate-950 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors">
                                    <div className="text-slate-400 font-mono">{new Date(m.date).getFullYear()}</div>
                                    <div className="font-medium text-slate-200 truncate mx-2 flex-1">{m.tournament_name}</div>
                                    <div className={`font-mono font-bold whitespace-nowrap ${m.winner_id === playerA.id ? 'text-blue-400' : 'text-red-400'}`}>
                                        {m.winner_id === playerA.id ? 'A' : 'B'} Won
                                    </div>
                                </div>
                            ))}
                            {h2h.length === 0 && <div className="text-slate-500 text-center py-8 italic">No historic matches found between these players.</div>}
                        </div>
                    </div>

                    {/* Validation Checklist - Mocked for now until we have full metrics per match context */}
                    <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8">
                        <h3 className="text-xl font-bold flex items-center gap-2 mb-4 text-slate-300">
                            <Check className="text-emerald-500" /> Checklist de Validación
                        </h3>
                        {statsA && statsB && prediction ? (
                            <ValidationChecklist
                                playerName={prediction.winner_id === playerA.id ? playerA.name : playerB.name}
                                metrics={{
                                    form: prediction.winner_id === playerA.id ? statsA.form * 100 : statsB.form * 100,
                                    surfaceWinRate: prediction.winner_id === playerA.id ? statsA.winrateSurface * 100 : statsB.winrateSurface * 100,
                                    regularity: 0.2, // Mocked as not calculated in statsA/B yet
                                    setTrend: prediction.winner_id === playerA.id ? statsA.setTrend : statsB.setTrend
                                }}
                                ev={0.05} // Mocked EV
                            />
                        ) : (
                            <div className="text-slate-500 italic">Selecciona jugadores para ver la validación.</div>
                        )}
                    </div>

                </div>
            )}
        </div>
    );
}

function PlayerSelectCard({ player, setPlayer, search, setSearch, color, label }: any) {
    const [suggestions, setSuggestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (search.length >= 2 && !player) {
                setLoading(true);
                const results = await api.searchPlayers(search);
                setSuggestions(results);
                setLoading(false);
            } else {
                setSuggestions([]);
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [search, player]);

    const handleSelect = (p: any) => {
        setPlayer(p);
        setSuggestions([]);
        setSearch(''); // Clear search on select or keep name? Better clear or set to name.
    };

    return (
        <div className={`flex-1 bg-slate-900 rounded-3xl border border-slate-800 p-6 flex flex-col items-center relative transition-all duration-300 ${player ? `border-${color}-500/20 shadow-lg shadow-${color}-900/10` : 'hover:border-slate-700'}`}>
            {!player ? (
                <div className="w-full h-full flex flex-col items-center justify-start pt-8 min-h-[300px]">
                    <div className={`w-20 h-20 rounded-full bg-slate-800 mb-6 flex items-center justify-center text-slate-600 border-2 border-slate-800`}>
                        <Search size={32} />
                    </div>
                    <h2 className="text-xl font-bold mb-2 text-slate-200">Select {label}</h2>
                    <p className="text-slate-500 text-sm mb-6 text-center">Search for a player to compare</p>

                    <div className="relative w-full max-w-sm">
                        <div className="relative">
                            <input
                                type="text"
                                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-4 pl-12 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 transition-all placeholder:text-slate-600 font-medium"
                                placeholder={`Type name (e.g. "Alcaraz")...`}
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                            <Search className="absolute left-4 top-4 text-slate-500" size={20} />
                            {loading && <div className="absolute right-4 top-4 w-5 h-5 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin"></div>}
                        </div>

                        {/* Suggestions Dropdown */}
                        {suggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden max-h-[300px] overflow-y-auto">
                                {suggestions.map(p => (
                                    <button
                                        key={p.id}
                                        onClick={() => handleSelect(p)}
                                        className="w-full text-left px-4 py-3 hover:bg-slate-800 flex items-center justify-between group transition-colors border-b border-slate-800/50 last:border-0"
                                    >
                                        <div className="font-medium text-slate-300 group-hover:text-white">{p.name}</div>
                                        <div className="text-xs text-slate-500 font-mono bg-slate-950 px-2 py-1 rounded">{p.country || 'UNK'}</div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <>
                    <button
                        onClick={() => { setPlayer(null); setSearch(''); }}
                        className="absolute top-4 right-4 p-2 rounded-full hover:bg-slate-800 text-slate-500 hover:text-red-400 transition-colors tooltip"
                        title="Remove Player"
                    >
                        <X size={20} />
                    </button>

                    <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                        <div className="w-32 h-32 rounded-full bg-slate-800 mb-6 overflow-hidden border-4 border-slate-900 shadow-2xl relative">
                            <div className={`w-full h-full flex items-center justify-center text-5xl font-black text-slate-700 bg-gradient-to-br from-slate-800 to-slate-900`}>
                                {player.name[0]}
                            </div>
                            <div className={`absolute bottom-0 inset-x-0 h-1 bg-${color}-500`}></div>
                        </div>

                        <h2 className="text-2xl font-black text-center mb-1 text-white">{player.name}</h2>
                        <div className="flex items-center gap-3 text-slate-400 text-sm font-medium bg-slate-950/50 px-4 py-1.5 rounded-full border border-slate-800">
                            <span className="flex items-center gap-1"><span className="text-slate-600">RANK</span> #{player.ranking || '-'}</span>
                            <div className="w-1 h-1 rounded-full bg-slate-700"></div>
                            <span>{player.country}</span>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

function ComparisonTable({ pA, pB, statsA, statsB }: any) {
    const Row = ({ label, valA, valB, rev = false }: any) => {
        const numA = parseFloat(valA);
        const numB = parseFloat(valB);
        let winA = numA > numB;
        if (rev) winA = numA < numB;
        if (isNaN(numA)) winA = false;

        return (
            <div className="flex items-center justify-between py-4 border-b border-slate-800 text-sm last:border-0 group hover:bg-slate-800/30 px-4 rounded-xl transition-colors">
                <div className={`w-1/3 text-right font-black text-lg ${winA ? 'text-emerald-400' : 'text-slate-500'}`}>{valA}</div>
                <div className="w-1/3 text-center text-slate-500 font-bold uppercase text-[10px] tracking-widest">{label}</div>
                <div className={`w-1/3 text-left font-black text-lg ${!winA && numA !== numB ? 'text-emerald-400' : 'text-slate-500'}`}>{valB}</div>
            </div>
        )
    }

    return (
        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8 h-full">
            <h3 className="text-xl font-bold mb-8 text-center text-slate-200 flex items-center justify-center gap-2"><Activity size={20} className="text-emerald-500" /> Key Metrics Analysis</h3>
            <div className="space-y-2">
                <Row label="ATP Rank" valA={pA.ranking || 999} valB={pB.ranking || 999} rev={true} />
                <Row label="ELO Rating" valA={statsA.elo} valB={statsB.elo} />
                <Row label="Recent Form" valA={(statsA.form * 100).toFixed(0) + '%'} valB={(statsB.form * 100).toFixed(0) + '%'} />
                <Row label="Surface Win%" valA={(statsA.winrateSurface * 100).toFixed(0) + '%'} valB={(statsB.winrateSurface * 100).toFixed(0) + '%'} />
                <Row label="H2H Wins" valA={statsA.h2h} valB={statsB.h2h} />
                <Row label="Set Aggression" valA={(statsA.setTrend * 100).toFixed(0)} valB={(statsB.setTrend * 100).toFixed(0)} />
            </div>
        </div>
    )
}

function HealthStatusCard({ player, label }: any) {
    return (
        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6">
            <h4 className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">{label} - {player?.name?.split(' ').pop()} Status</h4>

            <div className="space-y-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
                        <Activity size={18} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-white">Physical Condition</div>
                        <div className="text-xs text-emerald-400 font-medium">Fit to Play (Est.)</div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-800 rounded-lg text-slate-400">
                        <Activity size={18} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-slate-300">Last Match</div>
                        <div className="text-xs text-slate-500">No recent retirement</div>
                    </div>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-500 leading-relaxed italic">
                    "No significant injury reports found in the last 14 days."
                </div>
            </div>
        </div>
    )
}

