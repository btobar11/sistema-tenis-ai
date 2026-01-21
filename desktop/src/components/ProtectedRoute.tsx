import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Navigate, Outlet } from 'react-router-dom';
import { Loader2, AlertTriangle, LogOut } from 'lucide-react';

export default function ProtectedRoute() {
    const [loading, setLoading] = useState(true);
    const [session, setSession] = useState<any>(null);
    const [licenseValid, setLicenseValid] = useState<boolean>(false);
    const [statusMessage, setStatusMessage] = useState('');

    useEffect(() => {
        checkLicense();
    }, []);

    async function checkLicense() {
        const { data: sessionData } = await supabase.auth.getSession();

        if (!sessionData.session) {
            setLoading(false);
            return;
        }

        setSession(sessionData.session);

        // Validate Subscription via DB
        const { data: profile, error } = await supabase
            .from('profiles')
            .select('subscription_status, subscription_expires_at')
            .eq('id', sessionData.session.user.id)
            .single();

        if (error || !profile) {
            setLicenseValid(false);
            setStatusMessage('Error al verificar licencia.');
            setLoading(false);
            return;
        }

        const tier = profile.subscription_status;
        const now = new Date();
        const expires = profile.subscription_expires_at ? new Date(profile.subscription_expires_at) : null;

        if (tier === 'premium' || tier === 'trial') {
            if (expires && expires < now) {
                setLicenseValid(false);
                setStatusMessage('Tu licencia ha expirado. Por favor renueva en la web.');
            } else {
                setLicenseValid(true);
            }
        } else {
            setLicenseValid(false);
            setStatusMessage('Tu cuenta (Free) no tiene acceso al software descargable. Actualiza a Trial o Premium.');
        }

        setLoading(false);
    }

    async function handleLogout() {
        await supabase.auth.signOut();
        window.location.reload();
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            </div>
        );
    }

    if (!session) {
        return <Navigate to="/login" replace />;
    }

    if (!licenseValid) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-8 text-center">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Acceso Denegado</h2>
                <p className="text-slate-400 max-w-md mb-8">{statusMessage}</p>

                <button onClick={handleLogout} className="flex items-center gap-2 px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors">
                    <LogOut className="w-4 h-4" />
                    Cerrar Sesión
                </button>
            </div>
        )
    }

    return <Outlet />;
}
