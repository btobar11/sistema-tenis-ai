import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowLeft, History, XCircle, CheckCircle, DollarSign } from 'lucide-react';

interface BetEntry {
    id: string;
    bet_date: string;
    player_bet_on: string;
    opponent: string;
    tournament: string;
    surface: string;
    odds: number;
    stake: number;
    result: 'pending' | 'won' | 'lost' | 'void';
    profit_loss: number;
}

export default function MatchHistory() {
    const navigate = useNavigate();
    const [bets, setBets] = useState<BetEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'won' | 'lost' | 'pending'>('all');

    useEffect(() => {
        loadBets();
    }, [filter]);

    async function loadBets() {
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            let query = supabase
                .from('bet_journal')
                .select('*')
                .eq('user_id', user.id)
                .order('bet_date', { ascending: false });

            if (filter !== 'all') {
                query = query.eq('result', filter);
            }

            const { data, error } = await query;
            if (error) throw error;

            setBets(data || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    // Calculate stats
    const totalBets = bets.length;
    const wonBets = bets.filter(b => b.result === 'won').length;
    const lostBets = bets.filter(b => b.result === 'lost').length;
    const winRate = totalBets > 0 ? ((wonBets / (wonBets + lostBets)) * 100).toFixed(1) : '0.0';
    const totalPL = bets.reduce((sum, b) => sum + (b.profit_loss || 0), 0);
    const totalStaked = bets.reduce((sum, b) => sum + (b.stake || 0), 0);
    const roi = totalStaked > 0 ? ((totalPL / totalStaked) * 100).toFixed(1) : '0.0';

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            <div className="flex items-center gap-4 mb-8">
                <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                    <ArrowLeft />
                </button>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <History className="text-emerald-400" />
                    Betting Journal
                </h1>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-4 gap-6 mb-10">
                <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                    <div className="text-slate-400 text-sm mb-1">Win Rate</div>
                    <div className="text-3xl font-bold text-emerald-400">{winRate}%</div>
                    <div className="text-xs text-slate-500 mt-1">{wonBets}W - {lostBets}L</div>
                </div>
                <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                    <div className="text-slate-400 text-sm mb-1">ROI</div>
                    <div className={`text-3xl font-bold ${parseFloat(roi) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {parseFloat(roi) >= 0 ? '+' : ''}{roi}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Return on Investment</div>
                </div>
                <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                    <div className="text-slate-400 text-sm mb-1">Total P/L</div>
                    <div className={`text-3xl font-bold ${totalPL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {totalPL >= 0 ? '+' : ''}${totalPL.toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Profit/Loss</div>
                </div>
                <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                    <div className="text-slate-400 text-sm mb-1">Total Bets</div>
                    <div className="text-3xl font-bold text-white">{totalBets}</div>
                    <div className="text-xs text-slate-500 mt-1">All time</div>
                </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={() => setFilter('all')}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${filter === 'all' ? 'bg-emerald-500 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                >
                    All
                </button>
                <button
                    onClick={() => setFilter('won')}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${filter === 'won' ? 'bg-emerald-500 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                >
                    Won
                </button>
                <button
                    onClick={() => setFilter('lost')}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${filter === 'lost' ? 'bg-emerald-500 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                >
                    Lost
                </button>
                <button
                    onClick={() => setFilter('pending')}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${filter === 'pending' ? 'bg-emerald-500 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'
                        }`}
                >
                    Pending
                </button>
            </div>

            {/* Journal Table */}
            <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
                <div className="p-6 border-b border-slate-800">
                    <h2 className="font-bold text-lg">Bet History</h2>
                </div>

                {loading ? (
                    <div className="p-12 text-center text-slate-500">Loading...</div>
                ) : bets.length === 0 ? (
                    <div className="p-12 text-center">
                        <DollarSign className="w-12 h-12 text-slate-700 mx-auto mb-4" />
                        <p className="text-slate-500 mb-4">No bets recorded yet</p>
                        <p className="text-sm text-slate-600">Save bets from Match Analysis to track your performance</p>
                    </div>
                ) : (
                    <table className="w-full text-left">
                        <thead className="bg-slate-950/50 text-slate-400 text-sm uppercase">
                            <tr>
                                <th className="px-6 py-4 font-medium">Date</th>
                                <th className="px-6 py-4 font-medium">Match</th>
                                <th className="px-6 py-4 font-medium">Tournament</th>
                                <th className="px-6 py-4 font-medium">Odds</th>
                                <th className="px-6 py-4 font-medium">Stake</th>
                                <th className="px-6 py-4 font-medium">Result</th>
                                <th className="px-6 py-4 font-medium text-right">P/L</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {bets.map(bet => (
                                <tr key={bet.id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="px-6 py-4 text-slate-400 text-sm">
                                        {new Date(bet.bet_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium">{bet.player_bet_on}</div>
                                        <div className="text-sm text-slate-500">vs {bet.opponent}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">
                                        {bet.tournament}
                                        {bet.surface && <span className="ml-2 text-xs text-slate-600">({bet.surface})</span>}
                                    </td>
                                    <td className="px-6 py-4 font-mono text-sm">{bet.odds?.toFixed(2)}</td>
                                    <td className="px-6 py-4 font-mono text-sm">${bet.stake?.toFixed(2)}</td>
                                    <td className="px-6 py-4">
                                        {bet.result === 'won' ? (
                                            <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
                                                <CheckCircle size={16} /> WON
                                            </div>
                                        ) : bet.result === 'lost' ? (
                                            <div className="flex items-center gap-2 text-red-400 text-sm font-bold">
                                                <XCircle size={16} /> LOST
                                            </div>
                                        ) : (
                                            <div className="text-yellow-400 text-sm font-bold">PENDING</div>
                                        )}
                                    </td>
                                    <td className={`px-6 py-4 text-right font-mono font-bold ${bet.profit_loss >= 0 ? 'text-emerald-400' : 'text-red-400'
                                        }`}>
                                        {bet.profit_loss >= 0 ? '+' : ''}${bet.profit_loss?.toFixed(2)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
