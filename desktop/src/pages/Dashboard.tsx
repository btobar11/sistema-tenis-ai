import { useEffect, useState, cloneElement } from 'react';
import { api, type Match } from '../lib/api';
import { supabase } from '../lib/supabase';
import { Activity, Calendar, Search, ChevronRight, Zap, LogOut, Loader2, History as HistoryIcon, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MatchAnalysis from './MatchAnalysis';
import { BettingJournal } from './BettingJournal';
import ValidationChecklist from '../components/ValidationChecklist';
import AntiFomo from './AntiFomo';

export default function Dashboard({ initialView }: { initialView?: 'dashboard' | 'journal' | 'anti-fomo' | 'checklist' }) {
    // 1. View State
    const [activeView, setActiveView] = useState<'dashboard' | 'journal' | 'anti-fomo' | 'checklist'>(initialView || 'dashboard');
    const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);

    // 2. Data State
    const [matches, setMatches] = useState<Match[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterSurface, setFilterSurface] = useState<string>('all');
    const [filterDays, setFilterDays] = useState<number>(7);

    // 3. Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    const navigate = useNavigate();

    useEffect(() => {
        loadMatches();
    }, [filterDays]);

    // Debounced Search Effect
    useEffect(() => {
        const timeoutId = setTimeout(async () => {
            if (searchQuery.length >= 2) {
                setIsSearching(true);
                const results = await api.searchPlayers(searchQuery);
                setSearchResults(results);
                setIsSearching(false);
            } else {
                setSearchResults([]);
            }
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [searchQuery]);

    async function loadMatches() {
        try {
            setLoading(true);
            const data = await api.getUpcomingMatches(filterDays);
            setMatches(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    async function handleLogout() {
        await supabase.auth.signOut();
        navigate('/login');
    }

    function handleMatchSelect(matchId: string) {
        setSelectedMatchId(matchId);
        setActiveView('dashboard');
    }

    const filteredMatches = matches.filter(m =>
        filterSurface === 'all' || m.surface.toLowerCase() === filterSurface.toLowerCase()
    );

    // Group matches by date
    const matchesByDate = filteredMatches.reduce((acc: any, match) => {
        const date = new Date(match.date).toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        if (!acc[date]) acc[date] = [];
        acc[date].push(match);
        return acc;
    }, {});

    const renderContent = () => {
        switch (activeView) {
            case 'dashboard':
                return selectedMatchId ? (
                    <MatchAnalysis matchId={selectedMatchId} onBack={() => setSelectedMatchId(null)} />
                ) : (
                    <div className="space-y-6">
                        <header className="flex justify-between items-center">
                            <div>
                                <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                                <p className="text-slate-400">Selecciona un partido para analizar.</p>
                            </div>
                        </header>

                        {/* Filters */}
                        <div className="mb-6 space-y-3">
                            <div>
                                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">Período</label>
                                <div className="flex gap-2 overflow-x-auto pb-2">
                                    <FilterButton label="Hoy" active={filterDays === 1} onClick={() => setFilterDays(1)} />
                                    <FilterButton label="Mañana" active={filterDays === 2} onClick={() => setFilterDays(2)} />
                                    <FilterButton label="3 días" active={filterDays === 3} onClick={() => setFilterDays(3)} />
                                    <FilterButton label="7 días" active={filterDays === 7} onClick={() => setFilterDays(7)} />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">Superficie</label>
                                <div className="flex gap-2 overflow-x-auto pb-2">
                                    <FilterButton label="Todos" active={filterSurface === 'all'} onClick={() => setFilterSurface('all')} />
                                    <FilterButton label="Hard" active={filterSurface === 'hard'} onClick={() => setFilterSurface('hard')} />
                                    <FilterButton label="Clay" active={filterSurface === 'clay'} onClick={() => setFilterSurface('clay')} />
                                    <FilterButton label="Grass" active={filterSurface === 'grass'} onClick={() => setFilterSurface('grass')} />
                                </div>
                            </div>
                        </div>

                        {/* Matches List */}
                        <div className="space-y-6">
                            {loading ? (
                                <div className="text-center py-12 text-slate-500">Cargando partidos...</div>
                            ) : filteredMatches.length === 0 ? (
                                <div className="text-center py-12 text-slate-500">No hay partidos disponibles con este filtro.</div>
                            ) : (
                                Object.entries(matchesByDate).map(([date, dateMatches]: [string, any]) => (
                                    <div key={date}>
                                        <h3 className="text-sm font-semibold text-emerald-400 mb-3 uppercase tracking-wider">
                                            {date}
                                        </h3>
                                        <div className="space-y-4">
                                            {dateMatches.map((match: Match) => (
                                                <MatchCard key={match.id} match={match} onClick={() => handleMatchSelect(match.id)} />
                                            ))}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Disclaimer */}
                        <div className="mt-8 pt-6 border-t border-slate-800/50 text-center">
                            <p className="text-[10px] text-slate-600 max-w-2xl mx-auto">
                                DISCLAIMER: Este sistema proporciona análisis estadísticos basados en datos históricos. No garantiza resultados futuros ni constituye asesoría financiera. El usuario asume toda la responsabilidad por sus decisiones y el riesgo asociado.
                            </p>
                        </div>
                    </div>
                );
            case 'journal':
                return <BettingJournal />;
            case 'anti-fomo':
                return <AntiFomo />;
            case 'checklist':
                return <ValidationChecklist playerName="Demo" metrics={{ form: 80, surfaceWinRate: 70, regularity: 0.2, setTrend: 1 }} ev={0.15} />;
            default:
                return <div>View not found</div>;
        }
    };

    // State for User Profile
    const [userProfile, setUserProfile] = useState<{ email?: string, tier: string }>({ tier: 'free' });

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            if (user) {
                // FORCE CREATOR DISPLAY
                setUserProfile({ email: user.email, tier: 'creator' });
            }
        });
    }, []);

    const getTierBadge = () => {
        if (userProfile.tier === 'creator') return <span className="text-purple-400 text-xs font-bold flex items-center gap-1">✨ CREATOR MODE</span>;
        if (userProfile.tier === 'premium') return <span className="text-emerald-500 text-xs font-bold"> PREMIUM </span>;
        return <span className="text-slate-500 text-xs">Plan Gratuito</span>;
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white flex">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col shrink-0">
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-lg tracking-tight">EDGESET</span>
                </div>

                <nav className="space-y-2 flex-1">
                    <NavItem active={activeView === 'dashboard'} icon={<Calendar />} label="Partidos de Hoy" onClick={() => setActiveView('dashboard')} />
                    <NavItem active={activeView === 'journal'} icon={<HistoryIcon />} label="Journal de Apuestas" onClick={() => setActiveView('journal')} />
                    <NavItem active={activeView === 'anti-fomo'} icon={<Zap />} label="Anti-FOMO" onClick={() => setActiveView('anti-fomo')} />
                    <NavItem active={activeView === 'checklist'} icon={<CheckCircle2 />} label="Checklist Validación" onClick={() => setActiveView('checklist')} />
                </nav>

                <div className="pt-6 border-t border-slate-800">
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors mb-4"
                    >
                        <LogOut size={20} />
                        <span className="font-medium text-sm">Cerrar Sesión</span>
                    </button>

                    <div className="flex items-center gap-3 px-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${userProfile.tier === 'creator' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50' : 'bg-slate-800 text-slate-500'}`}>
                            {userProfile.email?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="text-sm overflow-hidden">
                            <div className="font-medium truncate max-w-[120px]" title={userProfile.email}>{userProfile.email?.split('@')[0] || 'Usuario'}</div>
                            {getTierBadge()}
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Search Header (Always visible) */}
                <div className="p-8 pb-0 shrink-0">
                    <div className="flex justify-end mb-4 relative z-50">
                        <div className="relative w-64">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Buscar jugador..."
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-emerald-500 transition-all focus:ring-1 focus:ring-emerald-500/50"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                            {isSearching && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
                                </div>
                            )}
                            {/* Search Results Dropdown */}
                            {(searchResults.length > 0 || (searchQuery.length >= 2 && !isSearching)) && (
                                <div className="absolute top-full right-0 mt-2 w-full bg-slate-900 border border-slate-800 rounded-xl shadow-xl overflow-hidden z-50">
                                    {searchResults.length > 0 ? (
                                        searchResults.map(player => (
                                            <button
                                                key={player.id}
                                                onClick={() => navigate(`/player/${player.id}`)}
                                                className="w-full text-left px-4 py-3 hover:bg-slate-800 flex items-center justify-between group"
                                            >
                                                <span className="font-medium text-slate-200 group-hover:text-white">{player.name}</span>
                                                {player.rank_single && <span className="text-xs text-slate-500">#{player.rank_single}</span>}
                                            </button>
                                        ))
                                    ) : (
                                        <div className="px-4 py-3 text-sm text-slate-500 text-center">No encontrado</div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Render Selected View */}
                <div className="flex-1 overflow-y-auto px-8 pb-8">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
}

function NavItem({ icon, label, active, onClick }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${active ? 'bg-emerald-500/10 text-emerald-400' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
        >
            {cloneElement(icon, { size: 20 })}
            <span className="font-medium text-sm">{label}</span>
        </button>
    )
}

function FilterButton({ label, active, onClick }: any) {
    return (
        <button
            onClick={onClick}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${active ? 'bg-emerald-500 border-emerald-500 text-white' : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'}`}
        >
            {label}
        </button>
    )
}

function MatchCard({ match, onClick }: { match: Match, onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-emerald-500/50 transition-all cursor-pointer hover:shadow-lg hover:shadow-emerald-500/5"
        >
            <div className="flex justify-between items-center gap-8">
                {/* Date & Tournament */}
                <div className="w-32 shrink-0">
                    <div className="text-xs font-bold text-emerald-500 uppercase tracking-wider mb-1">{match.surface}</div>
                    <div className="text-xs text-slate-400 truncate" title={match.tournament}>{match.tournament}</div>
                    <div className="text-xs text-slate-500 mt-2">{new Date(match.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>

                {/* Players */}
                <div className="flex-1 flex flex-col gap-3">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-mono text-slate-500 w-6">#{match.player_a.ranking}</span>
                            <span className="font-semibold text-lg">{match.player_a.name}</span>
                        </div>
                        {/* Fake Odds for Demo */}
                        <span className="text-xs text-slate-600 bg-slate-950 px-2 py-1 rounded">1.85</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-mono text-slate-500 w-6">#{match.player_b.ranking}</span>
                            <span className="font-semibold text-lg">{match.player_b.name}</span>
                        </div>
                        {/* Fake Odds for Demo */}
                        <span className="text-xs text-slate-600 bg-slate-950 px-2 py-1 rounded">1.95</span>
                    </div>
                </div>

                {/* Action */}
                <div className="shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-slate-800 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                    <ChevronRight size={20} />
                </div>
            </div>
        </div>
    )
}
