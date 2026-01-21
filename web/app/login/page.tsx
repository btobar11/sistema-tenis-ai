import AuthForm from '@/components/AuthForm'
import { Activity } from 'lucide-react'
import Link from 'next/link'

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
            <Link href="/" className="mb-8 flex items-center gap-2 text-white hover:text-emerald-400 transition-colors">
                <Activity className="w-6 h-6 text-emerald-500" />
                <span className="font-bold text-xl tracking-tight">EDGESET</span>
            </Link>
            <AuthForm type="login" />
            <p className="mt-8 text-xs text-slate-600 max-w-md text-center">
                Este software proporciona análisis estadísticos basados en datos históricos. No constituye asesoría financiera ni garantiza resultados. El usuario asume total responsabilidad.
            </p>
        </div>
    )
}
