'use client'

import React from 'react';
import { motion } from 'framer-motion';
import { Activity, BarChart2, Shield, Lock, ChevronRight, Zap, Target, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
};

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-white">
      {/* Navigation */}
      <nav className="fixed w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">EDGESET</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-emerald-400 transition-colors">Características</a>
            <a href="#philosophy" className="hover:text-emerald-400 transition-colors">Filosofía</a>
            <a href="#pricing" className="hover:text-emerald-400 transition-colors">Planes</a>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Iniciar Sesión
            </Link>
            <Link href="/register" className="text-sm font-bold bg-emerald-500 hover:bg-emerald-600 text-white px-5 py-2 rounded-lg transition-all shadow-lg shadow-emerald-500/20">
              Prueba Gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-emerald-500/10 rounded-full blur-[120px] -z-10" />

        <div className="max-w-7xl mx-auto px-6 text-center">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col items-center"
          >
            <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium text-emerald-400 mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              Professional Tennis Analysis Platform v1.0
            </motion.div>

            <motion.h1 variants={fadeInUp} className="text-5xl md:text-7xl font-bold tracking-tight mb-8 bg-gradient-to-br from-white via-slate-200 to-slate-500 bg-clip-text text-transparent">
              Decisiones basadas en datos.<br />
              <span className="text-emerald-500">No en emociones.</span>
            </motion.h1>

            <motion.p variants={fadeInUp} className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
              El software definitivo para el análisis de partidos de tenis.
              Elimina el ruido, gestiona el riesgo y descubre patrones ocultos con nuestro motor de checklist inteligente.
            </motion.p>

            <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row items-center gap-4">
              <Link href="/register" className="h-12 px-8 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/25">
                Comenzar Prueba de 7 Días <ChevronRight className="w-4 h-4" />
              </Link>
              <a href="#how-it-works" className="h-12 px-8 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-medium flex items-center gap-2 transition-all">
                Ver Demo
              </a>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Más que estadísticas simples</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">Nuestro motor no solo te dice quién gana más, sino quién es regular, quién está cansado y quién domina la superficie.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Shield className="w-6 h-6 text-emerald-400" />}
              title="Gestión de Riesgo"
              description="Semáforo automático (Verde/Amarillo/Rojo) calculado en base a 5 factores críticos. Evita partidos volátiles."
            />
            <FeatureCard
              icon={<Target className="w-6 h-6 text-blue-400" />}
              title="Checklist Inteligente"
              description="Evaluación automática de Forma, Superficie, Regularidad, Fatiga y Contexto para cada enfrentamiento."
            />
            <FeatureCard
              icon={<Zap className="w-6 h-6 text-amber-400" />}
              title="Anti-FOMO Meter"
              description="Nuestra tecnología exclusiva detecta cuando estás combinando demasiados eventos riesgosos."
            />
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h1 className="text-6xl md:text-7xl font-black tracking-tight mb-6 leading-tight">
              EDGE<span className="text-emerald-400">SET</span>
            </h1>
            <p className="block text-slate-400 text-3xl mt-4">Where data wins the set</p>
            <p className="text-slate-400">Sin contratos a largo plazo. Cancela cuando quieras.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Plan */}
            <PricingCard
              title="Free"
              price="$0"
              features={[
                "Acceso al Dashboard Web",
                "Ver partidos del día",
                "Sin análisis detallado",
                "Sin predicciones"
              ]}
              buttonText="Registrarse"
              buttonLink="/register"
              featured={false}
            />

            {/* Trial Plan */}
            <PricingCard
              title="Trial"
              price="Gratis / 7 días"
              features={[
                "Software Descargable PC/Mac",
                "3 Análisis diarios",
                "Semáforo de Riesgo",
                "Datos limitados (No H2H)",
                "1 chequeo Anti-FOMO/día"
              ]}
              buttonText="Iniciar Prueba"
              buttonLink="/register?plan=trial"
              featured={false}
            />

            {/* Premium Plan */}
            <PricingCard
              title="Pro"
              price="$29/mes"
              features={[
                "Acceso Ilimitado",
                "Todas las metricas desbloqueadas",
                "Análisis de Combinadas Ilimitado",
                "Historial completo",
                "Soporte Prioritario"
              ]}
              buttonText="Obtener Acceso Total"
              buttonLink="/register?plan=premium"
              featured={true}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-800 bg-slate-950 text-slate-500 text-sm">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-500" />
            <span className="font-semibold text-slate-300">Sistema Tenis</span>
          </div>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition-colors">Términos</a>
            <a href="#" className="hover:text-white transition-colors">Privacidad</a>
            <a href="#" className="hover:text-white transition-colors">Contacto</a>
          </div>
          <div>
            © 2026 Sistema Tenis. Todos los derechos reservados.
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:bg-slate-800/50">
      <div className="w-12 h-12 rounded-xl bg-slate-950 flex items-center justify-center mb-4 border border-slate-800">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-2 text-slate-200">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

function PricingCard({ title, price, features, buttonText, buttonLink, featured }: { title: string, price: string, features: string[], buttonText: string, buttonLink: string, featured: boolean }) {
  return (
    <div className={`p-8 rounded-3xl border flex flex-col ${featured ? 'bg-slate-900 border-emerald-500/50 relative overflow-hidden' : 'bg-slate-950 border-slate-800'}`}>
      {featured && (
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-400" />
      )}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-slate-400 mb-2">{title}</h3>
        <div className="text-4xl font-bold text-white">{price}</div>
      </div>
      <ul className="space-y-4 mb-8 flex-1">
        {features.map((feature, i) => (
          <li key={i} className="flex items-start gap-3 text-slate-300 text-sm">
            <TrendingUp className="w-5 h-5 text-emerald-500 shrink-0" />
            {feature}
          </li>
        ))}
      </ul>
      <Link href={buttonLink} className={`w-full py-3 rounded-xl font-bold text-center transition-all ${featured ? 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/25' : 'bg-slate-800 hover:bg-slate-700 text-slate-200'}`}>
        {buttonText}
      </Link>
    </div>
  );
}
