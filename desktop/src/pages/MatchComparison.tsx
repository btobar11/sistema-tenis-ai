import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Search, Trophy, Activity, Brain } from 'lucide-react';

export default function MatchComparison() {
    const [playerA, setPlayerA] = useState<any>(null);
    const [playerB, setPlayerB] = useState<any>(null);
    const [searchA, setSearchA] = useState('');
    const [searchB, setSearchB] = useState('');
    const [h2h, setH2h] = useState<any[]>([]);
    const [prediction, setPrediction] = useState<any>(null);

    // Mock search for MVP - replace with api.searchPlayers
    const handleSearch = async (query: string, setPlayer: any) => {
        if (query.length < 3) return;
        const results = await api.searchPlayers(query);
        if (results.length > 0) setPlayer(results[0]); // Auto-select first for demo
    };

    useEffect(() => {
        if (playerA && playerB) {
            loadComparison();
        }
    }, [playerA, playerB]);

    async function loadComparison() {
        // 1. Get H2H
        const history = await api.getHeadToHead(playerA.id, playerB.id);
        setH2h(history);

        // 2. Live AI Inference
        setPrediction(null);
        try {
            const aiResult = await api.predictMatch(playerA.id, playerB.id);
            if (aiResult) {
                // Map backend response to frontend view
                // Backend: { winner_id, confidence, reasoning, metrics }
                setPrediction({
                    winner_id: aiResult.winner_id,
                    confidence: aiResult.confidence,
                    // If backend sends reasoning string joined by |, split it
                    reasoning: aiResult.reasoning ? aiResult.reasoning.split(' | ') : ["Analysis complete based on live metrics."],
                    risk: aiResult.confidence > 0.75 ? "Low" : (aiResult.confidence > 0.6 ? "Medium" : "High")
                });
            }
        } catch (e) {
            console.error("AI Error", e);
        }
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            <h1 className="text-3xl font-bold text-center mb-12 flex items-center justify-center gap-3">
                <Activity className="text-emerald-500" />
                <span>Match Intelligence</span>
            </h1>

            {/* Players Selection / Header */}
            <div className="flex flex-col md:flex-row items-stretch gap-8 mb-12">
                {/* Player A Card */}
                <PlayerSelectCard
                    player={playerA}
                    setPlayer={setPlayerA}
                    search={searchA}
                    setSearch={setSearchA}
                    onSearch={() => handleSearch(searchA, setPlayerA)}
                    color="blue"
                    label="Player A"
                />

                {/* VS Badge */}
                <div className="flex flex-col items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center font-black text-2xl border-4 border-slate-900 shadow-xl z-10">
                        VS
                    </div>
                </div>

                {/* Player B Card */}
                <PlayerSelectCard
                    player={playerB}
                    setPlayer={setPlayerB}
                    search={searchB}
                    setSearch={setSearchB}
                    onSearch={() => handleSearch(searchB, setPlayerB)}
                    color="red"
                    label="Player B"
                />
            </div>

            {playerA && playerB && (
                <div className="max-w-5xl mx-auto space-y-12">

                    {/* AI Prediction Core */}
                    <div className="bg-slate-900/80 rounded-3xl border border-emerald-500/30 p-8 relative overflow-hidden backdrop-blur-sm">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500"></div>

                        <div className="flex flex-col md:flex-row gap-8">
                            <div className="flex-1">
                                <h3 className="text-emerald-400 font-bold tracking-wider text-sm uppercase mb-4 flex items-center gap-2">
                                    <Brain size={18} /> AI Prediction Model v2.1
                                </h3>
                                <div className="text-4xl font-bold text-white mb-2">
                                    {prediction?.winner_id === playerA.id ? playerA.name : playerB.name} <span className="text-emerald-500">to Win</span>
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

                            {/* Confidence Gauge Visual (Simplified) */}
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

                    {/* Tale of the Tape */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <ComparisonTable
                            pA={playerA}
                            pB={playerB}
                            statsA={{ elo: 1650, rank: 12, h2h: 3, form: 80 }}
                            statsB={{ elo: 1580, rank: 24, h2h: 1, form: 40 }}
                        />

                        {/* H2H History */}
                        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6">
                            <h3 className="text-lg font-bold mb-6 flex items-center gap-2"><Trophy size={18} className="text-amber-500" /> Head to Head ({h2h.length})</h3>
                            <div className="space-y-3">
                                {h2h.map((m: any) => (
                                    <div key={m.id} className="flex justify-between items-center text-sm p-3 bg-slate-950 rounded-xl border border-slate-800">
                                        <div className="text-slate-400">{new Date(m.date).getFullYear()}</div>
                                        <div className="font-medium text-slate-200">{m.tournament_name}</div>
                                        <div className={`font-mono font-bold ${m.winner_id === playerA.id ? 'text-blue-400' : 'text-red-400'}`}>
                                            {m.winner_id === playerA.id ? 'A' : 'B'} Won
                                        </div>
                                    </div>
                                ))}
                                {h2h.length === 0 && <div className="text-slate-500 text-center py-4">No match history.</div>}
                            </div>
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
}

function PlayerSelectCard({ player, setPlayer, search, setSearch, onSearch, color, label }: any) {
    return (
        <div className={`flex-1 bg-slate-900 rounded-3xl border border-slate-800 p-6 flex flex-col items-center relative overflow-hidden ${player ? `border-${color}-500/20` : ''}`}>
            {!player ? (
                <div className="w-full h-full flex flex-col items-center justify-center min-h-[300px]">
                    <h2 className="text-xl font-bold mb-4 text-slate-500">Select {label}</h2>
                    <div className="relative w-full max-w-xs">
                        <input
                            type="text"
                            className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                            placeholder="Search player..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                        />
                        <button onClick={onSearch} className="absolute right-3 top-3 text-slate-400 hover:text-emerald-500">
                            <Search size={20} />
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    <button onClick={() => setPlayer(null)} className="absolute top-4 right-4 text-slate-500 hover:text-white">✕</button>
                    <div className="w-32 h-32 rounded-2xl bg-slate-800 mb-6 overflow-hidden">
                        {/* Placeholder for Img */}
                        <div className={`w-full h-full flex items-center justify-center text-4xl font-bold text-slate-600 bg-${color}-500/10`}>
                            {player.name[0]}
                        </div>
                    </div>
                    <h2 className="text-3xl font-black text-center mb-2">{player.name}</h2>
                    <div className="flex gap-4 text-slate-400 text-sm font-medium">
                        <span>#{player.ranking || 'NR'}</span>
                        <span>{player.country}</span>
                    </div>
                </>
            )}
        </div>
    )
}

function ComparisonTable({ pA, pB, statsA, statsB }: any) {
    const Row = ({ label, valA, valB, rev = false }: any) => {
        const winA = rev ? valA < valB : valA > valB;
        return (
            <div className="flex items-center justify-between py-3 border-b border-slate-800 text-sm">
                <div className={`w-1/4 text-right font-bold ${winA ? 'text-blue-400' : 'text-slate-500'}`}>{valA}</div>
                <div className="w-1/2 text-center text-slate-400 font-medium uppercase text-xs tracking-wider">{label}</div>
                <div className={`w-1/4 text-left font-bold ${!winA ? 'text-red-400' : 'text-slate-500'}`}>{valB}</div>
            </div>
        )
    }

    return (
        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-6">
            <h3 className="text-lg font-bold mb-6 text-center text-slate-200">Tale of the Tape</h3>
            <div className="space-y-1">
                <Row label="ATP Rank" valA={pA.ranking} valB={pB.ranking} rev={true} />
                <Row label="ELO Rating" valA={statsA.elo} valB={statsB.elo} />
                <Row label="Recent Form" valA={statsA.form + '%'} valB={statsB.form + '%'} />
                <Row label="H2H Wins" valA={statsA.h2h} valB={statsB.h2h} />
                <Row label="Fatigue (Last 14d)" valA="Low" valB="High" />
            </div>
        </div>
    )
}
