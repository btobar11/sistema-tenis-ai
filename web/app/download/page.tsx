'use client'

import React from 'react';
import { Activity, Download } from 'lucide-react';
import Link from 'next/link';

export default function DownloadPage() {
    return (
        <div className="min-h-screen bg-slate-950">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <Activity className="w-6 h-6 text-emerald-500" />
                        <span className="font-bold text-lg text-white">EDGESET</span>
                    </Link>
                    <Link href="/dashboard" className="text-sm text-slate-400 hover:text-white transition-colors">
                        Dashboard
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-6 py-20">
                <div className="text-center mb-12">
                    <div className="w-20 h-20 bg-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <Download className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-5xl font-bold text-white mb-4">
                        Download EDGESET
                    </h1>
                    <p className="text-xl text-slate-400">
                        Professional Tennis Analysis Platform
                    </p>
                </div>

                {/* Download Card */}
                <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 mb-12">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-2">Windows Desktop Client</h2>
                            <p className="text-slate-400">Version 1.0.0</p>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-slate-500">File size</div>
                            <div className="text-white font-medium">~85 MB</div>
                        </div>
                    </div>

                    <button className="w-full flex items-center justify-center gap-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 mb-4">
                        <Download className="w-6 h-6" />
                        Download for Windows
                    </button>

                    <p className="text-xs text-slate-500 text-center">
                        Compatible with Windows 10 and Windows 11
                    </p>
                </div>

                {/* System Requirements */}
                <div className="grid md:grid-cols-2 gap-6 mb-12">
                    <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
                        <h3 className="font-bold text-white mb-4">System Requirements</h3>
                        <ul className="space-y-2 text-sm text-slate-400">
                            <li>• Windows 10/11 (64-bit)</li>
                            <li>• 4 GB RAM minimum</li>
                            <li>• 200 MB free disk space</li>
                            <li>• Internet connection required</li>
                        </ul>
                    </div>

                    <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
                        <h3 className="font-bold text-white mb-4">Installation</h3>
                        <ol className="space-y-2 text-sm text-slate-400">
                            <li>1. Download the installer</li>
                            <li>2. Run EDGESET-Setup.exe</li>
                            <li>3. Follow installation wizard</li>
                            <li>4. Launch and sign in</li>
                        </ol>
                    </div>
                </div>

                {/* Features */}
                <div className="p-8 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20">
                    <h3 className="text-2xl font-bold text-white mb-6">What's Included</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-white text-xs">✓</span>
                            </div>
                            <div>
                                <div className="font-medium text-white">Match Analysis</div>
                                <div className="text-sm text-slate-400">Deep statistical analysis with AI predictions</div>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-white text-xs">✓</span>
                            </div>
                            <div>
                                <div className="font-medium text-white">Real-time Data</div>
                                <div className="text-sm text-slate-400">Automated scraping from live tournaments</div>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-white text-xs">✓</span>
                            </div>
                            <div>
                                <div className="font-medium text-white">Risk Management</div>
                                <div className="text-sm text-slate-400">Kelly Criterion & portfolio optimization</div>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-white text-xs">✓</span>
                            </div>
                            <div>
                                <div className="font-medium text-white">Player Research</div>
                                <div className="text-sm text-slate-400">Comprehensive player profiles & stats</div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
