import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { Zap, TrendingUp, Target, ArrowRight, AlertTriangle, Lock, LogOut, Activity } from 'lucide-react'

// API base URL - should be configured via env in production
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Pick {
    id: string
    selection: string
    ev_percentage: number
    kelly_stake: number
    market_price: number
    model_probability: number
    bookmaker: string
    player_home: string
    player_away: string
    match: {
        id: string
        tournament: string
        surface: string
        date: string
        player_a_name: string
        player_b_name: string
    }
}

async function fetchDailyPicks(token: string): Promise<Pick[]> {
    try {
        const res = await fetch(`${API_URL}/daily-edge/picks?min_ev=3.0`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            cache: 'no-store'
        })

        if (!res.ok) {
            if (res.status === 402) {
                return []  // Premium required
            }
            throw new Error('Failed to fetch picks')
        }

        const data = await res.json()
        return data.picks || []
    } catch (error) {
        console.error('Error fetching daily picks:', error)
        return []
    }
}

export default async function DailyEdgePage() {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
        return redirect('/login')
    }

    // Get session token
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token || ''

    // Fetch profile to check subscription
    const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single()

    const tier = profile?.subscription_status || 'free'
    const isPremium = tier === 'premium' || tier === 'trial'

    let picks: Pick[] = []
    if (isPremium && token) {
        picks = await fetchDailyPicks(token)
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
                        <Link href="/dashboard" className="text-sm text-slate-400 hover:text-white">Dashboard</Link>
                        <Link href="/performance" className="text-sm text-slate-400 hover:text-white">Performance</Link>
                        <span className="text-sm text-slate-400">{user.email}</span>
                        <form action="/auth/signout" method="post">
                            <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                                <LogOut className="w-5 h-5" />
                            </button>
                        </form>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-12">
                {/* Page Title */}
                <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                        <Zap className="w-7 h-7 text-emerald-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">Daily Edge</h1>
                        <p className="text-slate-400">Value picks identified by our AI engine</p>
                    </div>
                </div>

                {!isPremium ? (
                    /* Paywall */
                    <div className="text-center py-20 bg-slate-900/50 rounded-3xl border border-slate-800">
                        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-6">
                            <Lock className="w-8 h-8 text-slate-500" />
                        </div>
                        <h2 className="text-2xl font-bold mb-4">Premium Feature</h2>
                        <p className="text-slate-400 mb-8 max-w-md mx-auto">
                            Daily Edge picks are available exclusively to Premium subscribers.
                            Upgrade now to access AI-powered value betting opportunities.
                        </p>
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center gap-2 px-8 py-3 bg-emerald-500 hover:bg-emerald-600 rounded-xl font-bold transition-all shadow-lg shadow-emerald-500/20"
                        >
                            Upgrade to Premium <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                ) : picks.length === 0 ? (
                    /* No Picks */
                    <div className="text-center py-20 bg-slate-900/50 rounded-3xl border border-slate-800">
                        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold mb-4">No Value Picks Today</h2>
                        <p className="text-slate-400 max-w-md mx-auto">
                            Our engine hasn't identified any picks meeting the EV threshold right now.
                            Check back later as new odds are scraped.
                        </p>
                    </div>
                ) : (
                    /* Picks Table */
                    <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-950">
                                    <tr>
                                        <th className="text-left px-6 py-4 text-sm font-semibold text-slate-400">Match</th>
                                        <th className="text-left px-6 py-4 text-sm font-semibold text-slate-400">Selection</th>
                                        <th className="text-center px-6 py-4 text-sm font-semibold text-slate-400">Odds</th>
                                        <th className="text-center px-6 py-4 text-sm font-semibold text-slate-400">EV%</th>
                                        <th className="text-center px-6 py-4 text-sm font-semibold text-slate-400">Kelly</th>
                                        <th className="text-center px-6 py-4 text-sm font-semibold text-slate-400">Confidence</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {picks.map((pick) => (
                                        <tr key={pick.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="font-medium text-white">
                                                    {pick.player_home} vs {pick.player_away}
                                                </div>
                                                <div className="text-sm text-slate-500">
                                                    {pick.match?.tournament || 'N/A'} • {pick.match?.surface || 'N/A'}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <Target className="w-4 h-4 text-emerald-400" />
                                                    <span className="font-semibold text-emerald-400">{pick.selection}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <span className="px-3 py-1 bg-slate-800 rounded-lg text-sm font-mono">
                                                    {pick.market_price?.toFixed(2)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={`px-3 py-1 rounded-lg text-sm font-bold ${pick.ev_percentage >= 10
                                                        ? 'bg-emerald-500/20 text-emerald-400'
                                                        : pick.ev_percentage >= 5
                                                            ? 'bg-amber-500/20 text-amber-400'
                                                            : 'bg-slate-700 text-slate-300'
                                                    }`}>
                                                    +{pick.ev_percentage?.toFixed(1)}%
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-center text-slate-300">
                                                {pick.kelly_stake?.toFixed(1)}%
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-emerald-500 rounded-full"
                                                            style={{ width: `${(pick.model_probability || 0) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-sm text-slate-400">
                                                        {((pick.model_probability || 0) * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Disclaimer */}
                <div className="mt-8 p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center">
                    <p className="text-xs text-slate-500">
                        ⚠️ <strong>Disclaimer:</strong> Past performance does not guarantee future results.
                        Betting involves risk. Please gamble responsibly.
                    </p>
                </div>
            </main>
        </div>
    )
}
