import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Navigate, Outlet } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function ProtectedRoute() {
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        checkAuth();
    }, []);

    async function checkAuth() {
        try {
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) {
                setLoading(false);
                return;
            }

            // Allow access to all authenticatd users
            // Ideally we would fetch profile here to check suspension, but for MVP/Launch
            // simply having a session is enough to enter the App. 
            // Feature gating is handled by specific pages (like MatchAnalysis).
            setUser(session.user);

        } catch (error) {
            console.error('Auth check error:', error);
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}
