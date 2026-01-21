# Sistema de Análisis de Tenis Profesional

Este repositorio contiene la implementación completa del sistema de análisis de tenis, incluyendo la plataforma web pública, el backend en Supabase y el cliente de escritorio seguro.

## Estructura del Proyecto

*   `/web`: Plataforma Pública (Next.js 14, Tailwind, Supabase Auth).
*   `/desktop`: Cliente de Escritorio (Electron, React, Vite).
*   `/supabase`: (Conceptual) Esquema de Base de Datos y Funciones RPC.

## 1. Configuración del Backend (Supabase)

Para desplegar este sistema, necesitas un proyecto en Supabase con las siguientes tablas y reglas.

### Tablas Principales
*   **matches**: Almacena partidos (ATP/WTA).
*   **players**: Información de jugadores.
*   **analysis_results**: Resultados del motor de análisis (picks, risk).
*   **profiles**: Datos de usuarios y estado de suscripción (`subscription_status`: 'free', 'trial', 'premium').

### Variables de Entorno
Crea un archivo `.env` en `/web` y `/desktop` con tus credenciales:

```env
NEXT_PUBLIC_SUPABASE_URL=tu_url_supabase
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key
```

## 2. Web Pública (Marketing & Auth)

La web maneja el registro y la gestión de cuentas.

*   **Instalación**: `cd web && npm install`
*   **Desarrollo**: `npm run dev`
*   **Características**: Landing Page Dark Premium, Login/Registro, Dashboard de Licencia.

## 3. Cliente de Escritorio (Software de Análisis)

El software core para los usuarios Premium. Incluye protección de licencia.

*   **Instalación**: `cd desktop && npm install`
*   **Desarrollo**: `npm run dev` (Abre la ventana de Electron).
*   **Construir Executable**: `npm run build` (Genera .exe en `/dist`).

### Módulos del Cliente
1.  **Dashboard**: Lista de partidos filtrable (Hard/Clay/Grass).
2.  **Match Analysis**: Vista detallada con Checklist visual y Semáforo de Riesgo.
3.  **Anti-FOMO**: Calculadora de riesgo para apuestas combinadas.
4.  **Historial**: Bitácora automática de picks (Journal).

## 4. Aspectos Legales (Importante)

Se ha implementado el **Disclaimer Legal** obligatorio en:
*   Web: Footer de Login y Registro.
*   Desktop: Pantalla de Login y Footer del Dashboard.

> *"Este software proporciona análisis estadísticos basados en datos históricos. No garantiza resultados futuros ni constituye asesoría financiera."*

## Próximos Pasos (Roadmap)

1.  **Carga de Datos**: Ejecutar scrapers para poblar la tabla `matches`.
2.  **Backtesting**: Validar el modelo con datos de 2023-2024.
3.  **Lanzamiento**: Desplegar Web en Vercel y distribuir el instalador Desktop.

---
© 2026 Sistema Tenis. Código Propietario.
