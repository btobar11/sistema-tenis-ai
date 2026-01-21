import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Zap, Plus, Trash2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface Pick {
    id: string;
    description: string;
    odds: number;
    risk: 'low' | 'medium' | 'high';
}

export default function AntiFomo() {
    const navigate = useNavigate();
    const [picks, setPicks] = useState<Pick[]>([]);
    const [description, setDescription] = useState('');
    const [odds, setOdds] = useState('');
    const [risk, setRisk] = useState<'low' | 'medium' | 'high'>('low');

    const addPick = () => {
        if (!description || !odds) return;
        setPicks([...picks, { id: Date.now().toString(), description, odds: parseFloat(odds), risk }]);
        setDescription('');
        setOdds('');
    };

    const removePick = (id: string) => {
        setPicks(picks.filter(p => p.id !== id));
    };

    // SRS Formula: Base Risk + (Extra_Picks * 10) + (High Risk Items * 20)
    const calculateTotalRisk = () => {
        if (picks.length === 0) return 0;

        let score = 0;

        // Base Risk (Avg of individual risks)
        const riskValues = { low: 10, medium: 35, high: 65 };
        const avgRisk = picks.reduce((acc, p) => acc + riskValues[p.risk], 0) / picks.length;
        score += avgRisk;

        // Penalize Combinations (Exponential-ish)
        if (picks.length > 1) {
            score += (picks.length - 1) * 15;
        }

        // Cap at 100
        return Math.min(100, Math.round(score));
    };

    const totalRisk = calculateTotalRisk();
    const riskLabel = totalRisk <= 30 ? 'Bajo' : totalRisk <= 60 ? 'Medio' : 'Alto';
    const riskColor = totalRisk <= 30 ? 'text-emerald-400' : totalRisk <= 60 ? 'text-amber-400' : 'text-red-400';

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8">
            <div className="flex items-center gap-4 mb-8">
                <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-900 rounded-full transition-colors text-slate-400 hover:text-white">
                    <ArrowLeft />
                </button>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Zap className="text-amber-400" />
                    Medidor Anti-FOMO
                </h1>
            </div>

            <div className="grid md:grid-cols-2 gap-12">
                {/* Visualizer */}
                <div className="order-2 md:order-1 flex flex-col items-center justify-center p-12 bg-slate-900 rounded-3xl border border-slate-800">
                    <div className="relative w-64 h-64 mb-8 flex items-center justify-center">
                        {/* Simple Gauge Visualization */}
                        <div className="w-full h-full rounded-full border-[20px] border-slate-800 relative flex items-center justify-center">
                            <div
                                className={`absolute inset-0 rounded-full border-[20px] ${totalRisk <= 30 ? 'border-emerald-500' : totalRisk <= 60 ? 'border-amber-500' : 'border-red-500'} transition-all duration-500`}
                                style={{ clipPath: `inset(${100 - totalRisk}% 0 0 0)` }} // Simplified visual logic
                            />
                            <div className="text-center">
                                <div className="text-6xl font-black mb-2">{totalRisk}</div>
                                <div className={`text-xl font-bold uppercase ${riskColor}`}>{riskLabel}</div>
                            </div>
                        </div>
                    </div>

                    <div className="text-center space-y-2">
                        <h3 className="text-xl font-bold">Diagnóstico</h3>
                        {totalRisk > 60 ? (
                            <p className="text-red-400 flex items-center gap-2 justify-center">
                                <AlertTriangle size={18} />
                                ¡Peligro de FOMO! Exceso de riesgo/picks.
                            </p>
                        ) : totalRisk > 30 ? (
                            <p className="text-amber-400 flex items-center gap-2 justify-center">
                                <AlertTriangle size={18} />
                                Precaución. Reduce el stake.
                            </p>
                        ) : (
                            <p className="text-emerald-400 flex items-center gap-2 justify-center">
                                <ShieldCheck size={18} />
                                Apuesta Inteligente Aprobada.
                            </p>
                        )}
                    </div>
                </div>

                {/* Controls */}
                <div className="order-1 md:order-2 space-y-8">
                    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
                        <h3 className="font-bold mb-4 text-slate-300">Agregar Selección</h3>
                        <div className="space-y-4">
                            <input
                                type="text"
                                placeholder="Descripción (Ej: Nadal gana 2-0)"
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 focus:outline-none focus:border-emerald-500"
                            />
                            <div className="flex gap-4">
                                <input
                                    type="number"
                                    placeholder="Cuota (Ej: 1.85)"
                                    value={odds}
                                    onChange={e => setOdds(e.target.value)}
                                    className="w-1/2 bg-slate-950 border border-slate-800 rounded-xl p-3 focus:outline-none focus:border-emerald-500"
                                />
                                <div className="flex-1 flex gap-2">
                                    {['low', 'medium', 'high'].map((r: any) => (
                                        <button
                                            key={r}
                                            onClick={() => setRisk(r)}
                                            className={`flex-1 rounded-xl capitalize text-sm font-bold border transition-all ${risk === r
                                                ? (r === 'low' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : r === 'medium' ? 'bg-amber-500/20 border-amber-500 text-amber-400' : 'bg-red-500/20 border-red-500 text-red-400')
                                                : 'border-slate-800 text-slate-500 hover:bg-slate-800'
                                                }`}
                                        >
                                            {r}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <button onClick={addPick} className="w-full py-3 bg-white text-slate-950 font-bold rounded-xl hover:bg-slate-200 transition-colors flex items-center justify-center gap-2">
                                <Plus size={18} />
                                Agregar
                            </button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {picks.map(pick => (
                            <div key={pick.id} className="flex items-center justify-between p-4 bg-slate-900 border border-slate-800 rounded-xl">
                                <div>
                                    <div className="font-medium text-white">{pick.description}</div>
                                    <div className="text-xs text-slate-500 flex gap-2">
                                        <span>Cuota: {pick.odds}</span>
                                        <span className={`uppercase font-bold ${pick.risk === 'low' ? 'text-emerald-500' : pick.risk === 'medium' ? 'text-amber-500' : 'text-red-500'}`}>{pick.risk} Risk</span>
                                    </div>
                                </div>
                                <button onClick={() => removePick(pick.id)} className="text-slate-600 hover:text-red-400 transition-colors">
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        ))}
                        {picks.length === 0 && (
                            <div className="text-center text-slate-600 py-4 italic">Agrega selecciones para calcular el riesgo...</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
