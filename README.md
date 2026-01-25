# 🎾 TENNIS INTELLIGENCE PLATFORM (SaaS + API)

> **Visión**: Plataforma SaaS de inteligencia deportiva especializada exclusivamente en tenis. No es una casa de apuestas; es una máquina de análisis, pricing probabilístico y detección de ineficiencias de mercado.

El sistema opera bajo un **Modelo Unificado B2B + B2C**: un solo core técnico, dos capas de acceso.

---

## 🏛️ Arquitectura General

*   **Backend**: Python 3.11 + FastAPI (ASGI).
*   **ML Engine**: XGBoost + scikit-learn (Calibración Platt).
*   **Database**: PostgreSQL 15 (Supabase).
*   **Frontend**: React 18 + TypeScript (Vite).
*   **Ingesta**: AsyncIO scrapers + The-Odds-API (Pinnacle/Bet365).

## 🔄 Pipeline de Datos (End-to-End)

1.  **Ingesta (The Sensors)**: Monitoreo live de partidos ATP/Challenger y cuotas de mercado.
2.  **Storage**: Normalización de entidades y esquemas `append-only` para auditoría financiera.
3.  **Feature Engineering**: ELO dinámico por superficie, Fatiga V2 (sets/viajes), Momentum.
4.  **Motor Predictivo (The Oracle)**: Modelos calibrados que emiten probabilidad real (0-1).
5.  **Value Engine (The Edge)**: Cálculo de EV (`Prob * Cuota - 1`) y Criterio de Kelly.
6.  **Trust Layer**: Ledger inmutable (`prediction_ledger`) que registra cada predicción para siempre.

## 💼 Modelo Híbrido: B2C vs B2B

La plataforma expone la misma inteligencia a dos audiencias:

### 🧍 B2C (Usuario Individual)
*   **Acceso**: Frontend Web Premium (`DailyDashboard`).
*   **Modelo**: Suscripción Mensual (Stripe).
*   **UX**: Insights explicados, filtros visuales, gráficas de rendimiento.
*   **Datos**: Pre-digeridos y filtrados por valor.

### 🏢 B2B (Enterprise / Fund)
*   **Acceso**: API REST (`/api/v1`) vía `X-API-Key`.
*   **Modelo**: Contrato Usage-Based (Billing por request).
*   **UX**: Datos crudos (JSON), endpoints de alta frecuencia.
*   **Datos**: Probabilidades sin redondear, series temporales completas.

---

## 🛠️ Estructura del Proyecto

```bash
/api            # FastAPI Backend (Routers, Middleware, Services)
/scrapers       # Motores de Ingesta Async (Matches + Odds)
/metrics        # Lógica de Negocio (ELO, Fatiga, Value Engine)
/ml             # Training Pipelines & Inference
/desktop        # Frontend Web (React/Vite)
/database       # Esquemas SQL (Migrations)
/scripts        # Utilidades (KeyGen, Backfill)
```

## 🔐 Seguridad & Confianza

*   **Ledger Inmutable**: `prediction_ledger` blindado por DB Triggers (Write-Once).
*   **Enterprise Auth**: Middleware de API Keys con Hashing SHA-256.
*   **Audit Logs**: Tabla `usage_logs` para facturación y auditoría.

---

**Estado:** Producción (v2.1)
**Stack:** Python • React • PostgreSQL • XGBoost
