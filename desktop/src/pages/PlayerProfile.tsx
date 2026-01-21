import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { ArrowLeft, Trophy, Activity, TrendingUp, MapPin } from 'lucide-react';

export default function PlayerProfile() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [player, setPlayer] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>(null);

    useEffect(() => {
        if (id) loadPlayer();
    }, [id]);

    async function loadPlayer() {
        setLoading(true);
        try {
            // 1. Get History (which contains player info in matches)
            const matchHistory = await api.getPlayerHistory(id!);
            if (matchHistory.length === 0) {
                setLoading(false);
                return;
            }

            setHistory(matchHistory);

            // Extract basic player info from the latest match
            const latestMatch = matchHistory[0];
            const playerInfo = latestMatch.player1_id === id ? latestMatch.player_a : latestMatch.player_b;

            // If API didn't expand relations, we might need a separate call or handle it differently
            // Assuming getPlayerHistory returns expanded matches as per our previous fix
            const info = {
                id: id,
                name: latestMatch.winner_id === id ? latestMatch.winner_name : (latestMatch.player1_id === id ? latestMatch.player_a?.name : latestMatch.player_b?.name), // Fallback
                ranking: latestMatch.player1_id === id ? latestMatch.player_a?.rank_single : latestMatch.player_b?.rank_single,
                country: latestMatch.player1_id === id ? latestMatch.player_a?.country : latestMatch.player_b?.country,
                hand: 'R' // Mock or fetch if available
            };

            // Better: if we had a getPlayerById in API. For now, infer from matches.
            setPlayer(playerInfo || info);

            // 2. Calculate Stats (Overall)
            const metrics = api.calculatePlayerMetrics(id!, info.name || 'Player', matchHistory, 'Hard'); // Default to Hard for general view or avg
            setStats(metrics);

        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-emerald-500">Cargando perfil...</div>;
    if (!player) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Jugador no encontrado</div>;

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            <button onClick={() => navigate(-1)} className="mb-6 p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                <ArrowLeft />
            </button>

            {/* Profile Header */}
            <div className="flex items-end gap-6 mb-12">
                <div className="w-24 h-24 bg-slate-800 rounded-2xl flex items-center justify-center text-4xl font-bold text-slate-600">
                    {player.name ? player.name.charAt(0) : '?'}
                </div>
                <div>
                    <h1 className="text-4xl font-bold mb-2">{player.name}</h1>
                    <div className="flex gap-4 text-slate-400 text-sm">
                        <span className="flex items-center gap-1"><Trophy size={14} /> ATP #{player.ranking || 'N/A'}</span>
                        <span className="flex items-center gap-1"><MapPin size={14} /> {player.country || player.nationality || 'Unknown'}</span>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <StatCard label="Forma Reciente" value={`${(stats.form * 100).toFixed(0)}%`} icon={<Activity />} color="emerald" />
                <StatCard label="Win Rate (Hard)" value={`${(stats.winrateSurface * 100).toFixed(0)}%`} icon={<TrendingUp />} color="blue" />
                <StatCard label="Set Wins" value={`${(stats.setTrend * 100).toFixed(0)}%`} icon={<Trophy />} color="amber" />
            </div>

            {/* Match History */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-6">
                <h3 className="text-xl font-bold mb-6">Historial Reciente</h3>
                <div className="space-y-4">
                    {history.slice(0, 10).map((match: any) => (
                        <div key={match.id} className="flex items-center justify-between p-4 bg-slate-950 rounded-xl border border-slate-800 hover:border-emerald-500/30 transition-colors">
                            <div className="flex flex-col">
                                <span className="text-emerald-500 text-xs font-bold uppercase mb-1">{match.surface}</span>
                                <span className="font-medium text-slate-300">{match.tournament_name}</span>
                            </div>
                            <div className="flex-1 px-8 text-center">
                                <span className="text-sm text-slate-500">vs</span>
                                <span className="font-bold ml-2">
                                    {match.player1_id === id ? match.player_b?.name : match.player_a?.name}
                                </span>
                            </div>
                            <div className="text-right">
                                <div className={`font-mono font-bold ${match.winner_id === id ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {match.score_full}
                                </div>
                                <div className="text-xs text-slate-600 mt-1">{new Date(match.date).toLocaleDateString()}</div>
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
