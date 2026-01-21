'use client'

import React, { useState } from 'react'
import { createClient } from '@/utils/supabase/client'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Lock, Mail, Loader2, ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface AuthFormProps {
    type: 'login' | 'register'
}

export default function AuthForm({ type }: AuthFormProps) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()
    const supabase = createClient()

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setLoading(true)
        setError(null)

        if (type === 'login') {
            const { error } = await supabase.auth.signInWithPassword({
                email,
                password,
            })
            if (error) {
                setError(error.message)
                setLoading(false)
            } else {
                router.push('/dashboard')
                router.refresh()
            }
        } else {
            const { error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: `${location.origin}/auth/callback`,
                },
            })
            if (error) {
                setError(error.message)
                setLoading(false)
            } else {
                setError('Check check your email to confirm account.')
                setLoading(false)
            }
        }
    }

    return (
        <div className="w-full max-w-md mx-auto p-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">
                    {type === 'login' ? 'Bienvenido de nuevo' : 'Crea tu cuenta'}
                </h2>
                <p className="text-slate-400 text-sm">
                    {type === 'login'
                        ? 'Ingresa tus credenciales para acceder al dashboard.'
                        : 'Comienza tu prueba gratuita de 7 días.'}
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
                    <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                        <input
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-slate-600"
                            placeholder="nombre@ejemplo.com"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Contraseña</label>
                    <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-slate-600"
                            placeholder="••••••••"
                        />
                    </div>
                </div>

                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2"
                    >
                        <span>⚠️ {error}</span>
                    </motion.div>
                )}

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <>
                            {type === 'login' ? 'Iniciar Sesión' : 'Registrarse'}
                            <ArrowRight className="w-4 h-4" />
                        </>
                    )}
                </button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-500">
                {type === 'login' ? (
                    <>
                        ¿No tienes cuenta?{' '}
                        <Link href="/register" className="text-emerald-400 hover:text-emerald-300 font-medium">
                            Regístrate gratis
                        </Link>
                    </>
                ) : (
                    <>
                        ¿Ya tienes cuenta?{' '}
                        <Link href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium">
                            Inicia sesión
                        </Link>
                    </>
                )}
            </div>
        </div>
    )
}
