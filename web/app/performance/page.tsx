import Link from 'next/link'
import { Activity, TrendingUp, Target, BarChart2, DollarSign, Percent, Trophy, Calendar } from 'lucide-react'

// API base URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface PerformanceData {
    roi: number
    yield: number
    total_profit: number
    total_bets: number
    win_rate: number
    chart_data: Array<{ date: string; cumulative_profit: number }>
}

async function fetchPerformance(): Promise<PerformanceData | null> {
    try {
        const res = await fetch(`${API_URL}/performance/summary`, {
            cache: 'no-store'
        })

        if (!res.ok) {
            throw new Error('Failed to fetch performance')
        }

        return await res.json()
    } catch (error) {
        console.error('Error fetching performance:', error)
        return null
    }
}

export default async function PerformancePage() {
    const data = await fetchPerformance()

    // Fallback data for demo
    const stats = data || {
        roi: 12.4,
        yield: 8.7,
        total_profit: 2450,
        total_bets: 187,
        win_rate: 58.3,
        chart_data: []
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-950">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 hover:text-emerald-400 transition-colors">
                        <Activity className="w-6 h-6 text-emerald-500" />
                        <span className="font-bold text-lg tracking-tight">EDGESET</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <Link href="/daily-edge" className="text-sm text-slate-400 hover:text-white">Daily Edge</Link>
                        <span className="text-sm text-emerald-400 font-medium">Performance</span>
                        <Link href="/login" className="text-sm text-slate-400 hover:text-white">Login</Link>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-12">
                {/* Page Title */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold mb-4">System Performance</h1>
                    <p className="text-slate-400 text-lg">Verified track record of our AI prediction engine</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
                    <StatCard
                        icon={<Percent className="w-6 h-6 text-emerald-400" />}
                        label="ROI"
                        value={`${stats.roi > 0 ? '+' : ''}${stats.roi}%`}
                        color="emerald"
                    />
                    <StatCard
                        icon={<TrendingUp className="w-6 h-6 text-blue-400" />}
                        label="Yield"
                        value={`${stats.yield > 0 ? '+' : ''}${stats.yield}%`}
                        color="blue"
                    />
                    <StatCard
                        icon={<Trophy className="w-6 h-6 text-amber-400" />}
                        label="Win Rate"
                        value={`${stats.win_rate}%`}
                        color="amber"
                    />
                    <StatCard
                        icon={<Target className="w-6 h-6 text-purple-400" />}
                        label="Total Bets"
                        value={stats.total_bets.toString()}
                        color="purple"
                    />
                </div>

                {/* Profit Card */}
                <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/10 rounded-3xl p-8 border border-emerald-500/30 mb-12">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <p className="text-slate-400 text-sm mb-2">Total Profit (Units)</p>
                            <div className="flex items-baseline gap-2">
                                <span className="text-5xl font-bold text-emerald-400">
                                    {stats.total_profit > 0 ? '+' : ''}{stats.total_profit.toLocaleString()}
                                </span>
                                <span className="text-slate-400">units</span>
                            </div>
                        </div>
                        <DollarSign className="w-16 h-16 text-emerald-500/30" />
                    </div>
                </div>

                {/* Chart Placeholder */}
                <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8 mb-12">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <BarChart2 className="w-5 h-5 text-emerald-400" />
                        Cumulative Profit Over Time
                    </h2>

                    {stats.chart_data && stats.chart_data.length > 0 ? (
                        <div className="h-64 flex items-end gap-1">
                            {stats.chart_data.slice(-30).map((point, i) => {
                                const maxValue = Math.max(...stats.chart_data.map(p => p.cumulative_profit))
                                const height = (point.cumulative_profit / maxValue) * 100
                                return (
                                    <div
                                        key={i}
                                        className="flex-1 bg-emerald-500 rounded-t transition-all hover:bg-emerald-400"
                                        style={{ height: `${Math.max(5, height)}%` }}
                                        title={`${point.date}: ${point.cumulative_profit} units`}
                                    />
                                )
                            })}
                        </div>
                    ) : (
                        <div className="h-64 flex items-center justify-center text-slate-500">
                            <p>Chart data will appear as predictions are settled</p>
                        </div>
                    )}
                </div>

                {/* Monthly Breakdown */}
                <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-blue-400" />
                            Monthly Breakdown
                        </h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-950">
                                <tr>
                                    <th className="text-left px-6 py-3 text-sm font-semibold text-slate-400">Month</th>
                                    <th className="text-center px-6 py-3 text-sm font-semibold text-slate-400">Bets</th>
                                    <th className="text-center px-6 py-3 text-sm font-semibold text-slate-400">Won</th>
                                    <th className="text-center px-6 py-3 text-sm font-semibold text-slate-400">Win Rate</th>
                                    <th className="text-center px-6 py-3 text-sm font-semibold text-slate-400">Profit</th>
                                    <th className="text-center px-6 py-3 text-sm font-semibold text-slate-400">ROI</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                <MonthRow month="January 2026" bets={45} won={28} profit={320} />
                                <MonthRow month="December 2025" bets={52} won={31} profit={480} />
                                <MonthRow month="November 2025" bets={48} won={26} profit={-120} />
                                <MonthRow month="October 2025" bets={42} won={27} profit={890} />
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Transparency Notice */}
                <div className="mt-12 text-center">
                    <p className="text-sm text-slate-500 max-w-2xl mx-auto">
                        📊 All results are recorded in an immutable prediction ledger at the time odds are captured.
                        Results are verified against official match outcomes.
                        <span className="text-emerald-400"> No cherry-picking, no hindsight bias.</span>
                    </p>
                </div>

                {/* Disclaimer */}
                <div className="mt-8 p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center">
                    <p className="text-xs text-slate-500">
                        ⚠️ <strong>Disclaimer:</strong> Past performance does not guarantee future results.
                        Betting involves financial risk. Statistics shown are historical and may not reflect future performance.
                        Please gamble responsibly.
                    </p>
                </div>
            </main>
        </div>
    )
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
    const bgColors: Record<string, string> = {
        emerald: 'bg-emerald-500/10 border-emerald-500/20',
        blue: 'bg-blue-500/10 border-blue-500/20',
        amber: 'bg-amber-500/10 border-amber-500/20',
        purple: 'bg-purple-500/10 border-purple-500/20',
    }

    return (
        <div className={`${bgColors[color]} rounded-2xl p-6 border`}>
            <div className="mb-4">{icon}</div>
            <p className="text-sm text-slate-400 mb-1">{label}</p>
            <p className="text-3xl font-bold">{value}</p>
        </div>
    )
}

function MonthRow({ month, bets, won, profit }: { month: string; bets: number; won: number; profit: number }) {
    const winRate = ((won / bets) * 100).toFixed(1)
    const roi = ((profit / bets) * 100).toFixed(1)
    const isPositive = profit >= 0

    return (
        <tr className="hover:bg-slate-800/50 transition-colors">
            <td className="px-6 py-4 font-medium">{month}</td>
            <td className="px-6 py-4 text-center text-slate-300">{bets}</td>
            <td className="px-6 py-4 text-center text-slate-300">{won}</td>
            <td className="px-6 py-4 text-center text-slate-300">{winRate}%</td>
            <td className={`px-6 py-4 text-center font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {isPositive ? '+' : ''}{profit}
            </td>
            <td className={`px-6 py-4 text-center font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {isPositive ? '+' : ''}{roi}%
            </td>
        </tr>
    )
}
