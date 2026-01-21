import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'
import { Download, Crown, Calendar, LogOut } from 'lucide-react'
import Link from 'next/link'

export default async function DashboardPage() {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
        return redirect('/login')
    }

    // Fetch profile
    const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single()

    const tier = profile?.subscription_status || 'free'
    const isPremium = tier === 'premium' || tier === 'trial'

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {/* Dashboard Header */}
            <header className="border-b border-slate-800 bg-slate-950">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="font-bold text-lg tracking-tight hover:text-emerald-400">EDGESET</Link>
                    <div className="flex items-center gap-4">
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
                <h1 className="text-3xl font-bold mb-8">User Dashboard</h1>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Status Card */}
                    <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-10">
                            <Crown className="w-32 h-32 text-emerald-500" />
                        </div>

                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            <Crown className={`w-6 h-6 ${isPremium ? 'text-emerald-400' : 'text-slate-500'}`} />
                            Subscription Status
                        </h2>

                        <div className="mb-6">
                            <div className="text-sm text-slate-400 mb-1">Current Plan</div>
                            <div className="text-4xl font-bold capitalize text-white">
                                {tier === 'trial' ? 'Free Trial' : tier}
                            </div>
                        </div>

                        {tier === 'free' ? (
                            <Link href="/pricing" className="block w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-center font-bold text-white transition-all shadow-lg shadow-emerald-500/20">
                                Upgrade to Premium
                            </Link>
                        ) : (
                            <div className="flex items-center gap-3 text-slate-300 bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                                <Calendar className="w-5 h-5 text-emerald-500" />
                                <span>Expires: {profile?.subscription_expires_at ? new Date(profile.subscription_expires_at).toLocaleDateString() : 'N/A'}</span>
                            </div>
                        )}
                    </div>

                    {/* Download Card */}
                    <div className={`p-8 rounded-3xl border transition-all ${isPremium ? 'bg-slate-900 border-slate-800' : 'bg-slate-950 border-slate-900 opacity-50 grayscale'}`}>
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            <Download className="w-6 h-6 text-blue-400" />
                            Desktop Client
                        </h2>

                        <p className="text-slate-400 mb-8 leading-relaxed">
                            Download the official EDGESET desktop application for Windows to access real-time match analysis, intelligent checklists, and risk management tools.
                        </p>

                        {isPremium ? (
                            <Link href="/download" className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2">
                                <Download className="w-5 h-5" />
                                Download for Windows (v1.0)
                            </Link>
                        ) : (
                            <button disabled className="w-full py-3 rounded-xl bg-slate-800 text-slate-500 font-bold cursor-not-allowed flex items-center justify-center gap-2">
                                <LockIcon className="w-4 h-4" />
                                Requires Active Subscription
                            </button>
                        )}
                    </div>
                </div>
            </main>
        </div>
    )
}

function LockIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
    )
}
