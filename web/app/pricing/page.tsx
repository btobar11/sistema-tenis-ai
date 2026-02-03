import Link from 'next/link'
import { Check, ArrowRight, Shield, Zap, Activity, Building2 } from 'lucide-react'
import { createClient } from '@/utils/supabase/server'
import CheckoutButtons from './CheckoutButtons'

export default async function PricingPage() {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-emerald-500 selection:text-slate-950">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-950 sticky top-0 z-10 backdrop-blur-md bg-opacity-90">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                        <div className="w-8 h-8 bg-emerald-600 rounded-sm flex items-center justify-center">
                            <Activity className="w-5 h-5 text-slate-950" />
                        </div>
                        <div className="flex flex-col">
                            <span className="font-bold text-lg tracking-tight leading-none">EDGESET</span>
                            <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">Quantitative Intelligence</span>
                        </div>
                    </Link>
                    <div className="flex items-center gap-6">
                        <Link href="/daily-edge" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">DAILY EDGE</Link>
                        {user ? (
                            <Link href="/dashboard" className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm font-medium transition-colors">
                                Dashboard
                            </Link>
                        ) : (
                            <Link href="/login" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
                                Login
                            </Link>
                        )}
                    </div>
                </div>
            </header>

            <main className="py-24">
                <div className="max-w-7xl mx-auto px-6">
                    {/* Hero Section */}
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <h1 className="text-5xl font-bold tracking-tight mb-6 bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                            Quantitative Intelligence<br />for Sports Markets
                        </h1>
                        <p className="text-xl text-slate-400 font-light mb-8 leading-relaxed">
                            Identify probabilistic inefficiencies using transparent models.<br />
                            EDGESET surfaces signals, not advice.
                        </p>
                    </div>

                    {/* Pricing Grid */}
                    <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">

                        {/* FREE TIER */}
                        <div className="border border-slate-800 bg-slate-900/50 rounded-2xl p-8 flex flex-col hover:border-slate-700 transition-all">
                            <div className="mb-8">
                                <div className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4">Observation</div>
                                <h3 className="text-2xl font-bold text-white mb-2">Market Overview</h3>
                                <p className="text-slate-400 text-sm">Observe the market. Understand where value exists. No signals. No execution.</p>
                            </div>
                            <div className="mb-8 font-mono text-3xl font-bold">Free</div>
                            <ul className="space-y-4 mb-8 flex-1">
                                <FeatureItem text="Daily Market Status" />
                                <FeatureItem text="Volume Analysis (ATP/WTA)" />
                                <FeatureItem text="1 Anonymized Example/Week" />
                                <FeatureItem text="Historical Performance Data" />
                                <FeatureItem text="No Actionable Signals" faded />
                            </ul>
                            <Link href="/register" className="w-full block text-center py-3 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white transition-all font-medium">
                                Create Account
                            </Link>
                        </div>

                        {/* PRO TIER - FEATURED */}
                        <div className="border border-emerald-500/30 bg-slate-900 rounded-2xl p-8 flex flex-col relative shadow-2xl shadow-emerald-900/10">
                            <div className="absolute top-0 right-0 left-0 h-1 bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-t-2xl"></div>
                            <div className="mb-8">
                                <div className="text-sm font-mono text-emerald-500 uppercase tracking-widest mb-4">Execution</div>
                                <h3 className="text-2xl font-bold text-white mb-2">Quantitative Signals</h3>
                                <p className="text-slate-400 text-sm">Probabilistic signals, not predictions. Designed for disciplined decision-makers.</p>
                            </div>
                            <div className="mb-8">
                                <span className="font-mono text-4xl font-bold text-white">$29</span>
                                <span className="text-slate-500">/month</span>
                            </div>
                            <ul className="space-y-4 mb-8 flex-1">
                                <FeatureItem text="Daily Edge Signals (Full Access)" highlighted />
                                <FeatureItem text="EV%, Odds & Confidence Scores" highlighted />
                                <FeatureItem text="Quarter-Kelly Staking Guide" />
                                <FeatureItem text="Engine Transparency Report" />
                                <FeatureItem text="Validation Report (Read-only)" />
                                <FeatureItem text="Personal Signal History" />
                            </ul>
                            {/* Checkout Buttons */}
                            <CheckoutButtons
                                monthlyPriceId="price_1SwTGrEJ5pLsQcZ3WxfudcCz"
                                yearlyPriceId="price_1SwTGrEJ5pLsQcZ3gIc4BtvD"
                            />
                            <p className="text-center text-xs text-slate-500 mt-4 font-mono">No predictions. No emotion. Just data.</p>
                        </div>

                        {/* INSTITUTIONAL TIER */}
                        <div className="border border-slate-800 bg-slate-900/50 rounded-2xl p-8 flex flex-col hover:border-slate-700 transition-all">
                            <div className="mb-8">
                                <div className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4">Infrastructure</div>
                                <h3 className="text-2xl font-bold text-white mb-2">Edge Infrastructure</h3>
                                <p className="text-slate-400 text-sm">Quantitative market signals for research, trading and risk teams.</p>
                            </div>
                            <div className="mb-8 font-mono text-3xl font-bold">Custom</div>
                            <ul className="space-y-4 mb-8 flex-1">
                                <FeatureItem text="API Access (Direct Feed)" />
                                <FeatureItem text="Historical Datasets (CSV/JSON)" />
                                <FeatureItem text="Custom EV Thresholds" />
                                <FeatureItem text="SLA + Uptime Guarantee" />
                                <FeatureItem text="Audit Logs & Compliance" />
                            </ul>
                            <a href="mailto:institutional@edgeset.com" className="w-full block text-center py-3 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white transition-all font-medium">
                                Contact Sales
                            </a>
                        </div>
                    </div>

                    {/* Footer Disclaimer */}
                    <div className="mt-24 pt-8 border-t border-slate-800 text-center max-w-2xl mx-auto">
                        <p className="text-xs text-slate-500 leading-relaxed">
                            <strong>Disclaimer:</strong> EDGESET provides analytical information only. No financial or wagering advice is given.
                            Past performance is not indicative of future results. Trading sports markets involves substantial risk.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    )
}

function FeatureItem({ text, highlighted = false, faded = false }: { text: string, highlighted?: boolean, faded?: boolean }) {
    return (
        <li className={`flex items-start gap-3 ${faded ? 'opacity-50' : ''}`}>
            <div className={`mt-1 w-4 h-4 rounded-full flex items-center justify-center ${highlighted ? 'bg-emerald-500/20' : 'bg-slate-800'}`}>
                <Check className={`w-3 h-3 ${highlighted ? 'text-emerald-500' : 'text-slate-400'}`} />
            </div>
            <span className={`text-sm ${highlighted ? 'text-white font-medium' : 'text-slate-300'}`}>{text}</span>
        </li>
    )
}
