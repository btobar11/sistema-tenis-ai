import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { ArrowLeft, Trophy, Activity, TrendingUp, MapPin, Zap } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';

export default function PlayerProfile() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [player, setPlayer] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>(null);
    const [eloHistory, setEloHistory] = useState<any[]>([]);

    useEffect(() => {
        if (id) loadPlayer();
    }, [id]);

    async function loadPlayer() {
        setLoading(true);
        try {
            const matchHistory = await api.getPlayerHistory(id!);
            if (matchHistory.length === 0) {
                setLoading(false);
                return;
            }

            setHistory(matchHistory);

            const latestMatch = matchHistory[0];
            const playerInfo = latestMatch.player1_id === id ? latestMatch.player_a : latestMatch.player_b;

            const info = {
                id: id,
                name: latestMatch.winner_id === id ? latestMatch.winner_name : (latestMatch.player1_id === id ? latestMatch.player_a?.name : latestMatch.player_b?.name),
                ranking: latestMatch.player1_id === id ? latestMatch.player_a?.rank_single : latestMatch.player_b?.rank_single,
                country: latestMatch.player1_id === id ? latestMatch.player_a?.country : latestMatch.player_b?.country,
            };

            setPlayer(playerInfo || info);

            const metrics = api.calculatePlayerMetrics(id!, info.name || 'Player', matchHistory, 'Hard');
            setStats(metrics);

            // Fetch Real ELO History
            const realEloHistory = await api.getPlayerEloHistory(id!);
            // Format for chart: { date: 'YYYY-MM-DD', elo: 1500 }
            // API returns reversed (oldest first)? Let's check service. Python does list(reversed(history)).
            // So [Oldest ... Newest]. Good for chart.

            const formattedElo = realEloHistory.length > 0
                ? realEloHistory.map((h: any) => ({
                    date: new Date(h.date).toLocaleDateString(),
                    elo: Math.round(h.elo)
                }))
                : [{ date: 'Today', elo: 1500 }]; // Fallback

            setEloHistory(formattedElo);

        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-emerald-500 font-mono">Loading Intelligence Engine...</div>;
    if (!player) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Jugador no encontrado</div>;

    // Radar Data
    const radarData = [
        { subject: 'Forma', A: (stats?.form || 0.5) * 100, fullMark: 100 },
        { subject: 'Regularidad', A: (stats?.regularity || 0.5) * 100, fullMark: 100 },
        { subject: 'Hard', A: (stats?.winrateSurface || 0.5) * 100, fullMark: 100 },
        { subject: 'Sets', A: (stats?.setTrend || 0.5) * 100, fullMark: 100 },
        { subject: 'Clutch', A: 65, fullMark: 100 }, // Placeholder
    ];

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            <button onClick={() => navigate(-1)} className="mb-6 p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                <ArrowLeft />
            </button>

            {/* Profile Header */}
            <div className="flex flex-col md:flex-row items-end gap-8 mb-12">
                <div className="w-32 h-32 bg-slate-800 rounded-2xl flex items-center justify-center text-5xl font-bold text-slate-600 overflow-hidden relative border-4 border-slate-900 shadow-2xl">
                    {player.photo_url ? (
                        <img src={player.photo_url} alt={player.name} className="w-full h-full object-cover" />
                    ) : (
                        player.name ? player.name.charAt(0) : '?'
                    )}
                </div>
                <div className="flex-1">
                    <h1 className="text-5xl font-black mb-4 tracking-tight">{player.name}</h1>
                    <div className="flex flex-wrap gap-6 text-slate-400 font-medium">
                        <span className="flex items-center gap-2 px-3 py-1 bg-slate-900 rounded-lg border border-slate-800"><Trophy size={16} className="text-emerald-500" /> ATP #{player.ranking || 'N/A'}</span>
                        <span className="flex items-center gap-2 px-3 py-1 bg-slate-900 rounded-lg border border-slate-800"><MapPin size={16} className="text-blue-500" /> {player.country || 'Unknown'}</span>
                        <span className="flex items-center gap-2 px-3 py-1 bg-slate-900 rounded-lg border border-slate-800"><Zap size={16} className="text-amber-500" /> ELO: 1640 (Est.)</span>
                    </div>
                </div>
            </div>

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">

                {/* 1. ELO Evolution Chart */}
                <div className="lg:col-span-2 bg-slate-900/50 rounded-3xl border border-slate-800 p-8 relative overflow-hidden">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold flex items-center gap-2"><Activity className="text-emerald-500" /> Evolución ELO (6 Meses)</h3>
                        <span className="text-xs font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded">LIVE METRICS</span>
                    </div>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={eloHistory}>
                                <defs>
                                    <linearGradient id="colorElo" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" hide />
                                <YAxis domain={['auto', 'auto']} hide />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                                    itemStyle={{ color: '#10b981' }}
                                />
                                <Area type="monotone" dataKey="elo" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorElo)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Stats Radar */}
                <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8 flex flex-col items-center justify-center">
                    <h3 className="text-xl font-bold mb-4 w-full text-left">Perfil Técnico</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                <PolarGrid stroke="#334155" />
                                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Radar name="Player" dataKey="A" stroke="#3b82f6" strokeWidth={3} fill="#3b82f6" fillOpacity={0.4} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Quick Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
                <StatCard label="Forma (10p)" value={stats?.form ? `${(stats.form * 100).toFixed(0)}%` : 'N/A'} icon={<Activity />} color="emerald" />
                <StatCard label="Fatiga" value="Media" sub="6 partidos / 14d" icon={<Zap />} color="amber" />
                <StatCard label="Hard Win%" value={stats?.winrateSurface ? `${(stats.winrateSurface * 100).toFixed(0)}%` : 'N/A'} icon={<TrendingUp />} color="blue" />
                <StatCard label="Volatilidad" value="Baja" icon={<Activity />} color="purple" />
            </div>

            {/* Match History */}
            <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8">
                <h3 className="text-xl font-bold mb-6">Historial de Partidos</h3>
                <div className="space-y-4">
                    {history.slice(0, 10).map((match: any) => (
                        <div key={match.id} className="flex items-center justify-between p-4 bg-slate-950 rounded-xl border border-slate-800 hover:border-emerald-500/30 transition-all group">
                            <div className="flex items-center gap-4 w-1/3">
                                <div className={`w-2 h-12 rounded-full ${match.winner_id === id ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                                <div>
                                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">{match.surface || 'HARD'}</div>
                                    <div className="font-semibold text-slate-200">{match.tournament_name || 'Tournament'}</div>
                                </div>
                            </div>

                            <div className="font-bold text-lg text-slate-400">VS</div>

                            <div className="w-1/3 text-right">
                                <div className="font-bold text-white mb-1">
                                    {match.player1_id === id ? (match.player_b?.name || match.player2_name) : (match.player_a?.name || match.player1_name)}
                                </div>
                                <div className={`font-mono ${match.winner_id === id ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {match.score_full || match.score || 'N/A'}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function StatCard({ label, value, icon, color }: any) {
    const colors: any = {
        emerald: "bg-emerald-500/10 text-emerald-400",
        blue: "bg-blue-500/10 text-blue-400",
        amber: "bg-amber-500/10 text-amber-400",
    }

    return (
        <div className={`p-6 rounded-2xl border border-slate-800 flex items-center gap-4 ${colors[color]}`}>
            <div className="p-3 bg-slate-950/50 rounded-xl">
                {icon}
            </div>
            <div>
                <div className="text-sm opacity-70 mb-1">{label}</div>
                <div className="text-3xl font-bold">{value}</div>
            </div>
        </div>
    )
}
