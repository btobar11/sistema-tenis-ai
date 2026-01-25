import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { History } from 'lucide-react';

export function BettingJournal() {
    const [bets, setBets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ totalProfit: 0, roi: 0, winRate: 0, totalBets: 0 });

    useEffect(() => {
        loadBets();
    }, []);

    async function loadBets() {
        try {
            const data = await api.getUserBets();
            setBets(data);
            calculateStats(data);
        } catch (e) {
            console.error("Failed to load bets", e);
        } finally {
            setLoading(false);
        }
    }

    function calculateStats(data: any[]) {
        const finishedBets = data.filter(b => b.status !== 'pending');
        const wonBets = finishedBets.filter(b => b.status === 'won');
        const totalInvested = finishedBets.reduce((sum, b) => sum + Number(b.amount), 0);
        const totalProfit = finishedBets.reduce((sum, b) => sum + (b.status === 'won' ? (Number(b.amount) * Number(b.odds)) - Number(b.amount) : -Number(b.amount)), 0);

        setStats({
            totalProfit,
            roi: totalInvested > 0 ? (totalProfit / totalInvested) * 100 : 0,
            winRate: finishedBets.length > 0 ? (wonBets.length / finishedBets.length) * 100 : 0,
            totalBets: data.length
        });
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        <History className="text-emerald-500" />
                        Journal de Apuestas
                    </h1>
                    <p className="text-slate-400">Tu historial de rendimiento y contabilidad.</p>
                </div>
            </header>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <div className="text-slate-400 text-sm mb-1">Profit Total</div>
                    <div className={`text-2xl font-bold ${stats.totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        ${stats.totalProfit.toFixed(2)}
                    </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <div className="text-slate-400 text-sm mb-1">ROI</div>
                    <div className={`text-2xl font-bold ${stats.roi >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {stats.roi.toFixed(1)}%
                    </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <div className="text-slate-400 text-sm mb-1">Win Rate</div>
                    <div className="text-2xl font-bold text-white">
                        {stats.winRate.toFixed(1)}%
                    </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <div className="text-slate-400 text-sm mb-1">Total Bets</div>
                    <div className="text-2xl font-bold text-white">
                        {stats.totalBets}
                    </div>
                </div>
            </div>

            {/* Bets List */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-slate-800 bg-slate-800/30">
                    <h3 className="font-semibold text-white">Historial Reciente</h3>
                </div>

                {bets.length === 0 ? (
                    <div className="p-8 text-center text-slate-500">
                        {loading ? "Cargando..." : "No hay apuestas registradas aún."}
                    </div>
                ) : (
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-slate-800/50 text-xs uppercase font-medium text-slate-500">
                            <tr>
                                <th className="px-6 py-3">Fecha</th>
                                <th className="px-6 py-3">Partido</th>
                                <th className="px-6 py-3">Pick</th>
                                <th className="px-6 py-3">Cuota</th>
                                <th className="px-6 py-3">Stake</th>
                                <th className="px-6 py-3">Resultado</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {bets.map((bet) => (
                                <tr key={bet.id} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="px-6 py-4">{new Date(bet.created_at).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 text-white">
                                        {bet.match?.player_a?.name} vs {bet.match?.player_b?.name}
                                    </td>
                                    <td className="px-6 py-4">
                                        {/* Simplified logic to show picked name if possible, else ID */}
                                        <span className="text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 rounded text-xs">
                                            Picked
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-mono">{bet.odds}</td>
                                    <td className="px-6 py-4">${bet.amount}</td>
                                    <td className="px-6 py-4">
                                        {bet.status === 'pending' && <span className="text-amber-400 bg-amber-500/10 px-2 py-1 rounded-full text-xs">Pendiente</span>}
                                        {bet.status === 'won' && <span className="text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full text-xs">+${(bet.amount * bet.odds - bet.amount).toFixed(2)}</span>}
                                        {bet.status === 'lost' && <span className="text-red-400 bg-red-500/10 px-2 py-1 rounded-full text-xs">-${bet.amount}</span>}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
