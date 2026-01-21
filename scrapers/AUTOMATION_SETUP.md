# Automated Tennis Match Scraper Setup

## 📋 Configuración Completada

✅ Credenciales de Supabase configuradas en `.env`
✅ Dependencias Python instaladas (requests, beautifulsoup4, python-dotenv)
✅ Scraper probado y funcionando

## 🤖 Automatización con Windows Task Scheduler

### Paso 1: Crear la Tarea Programada

1. Abre **Task Scheduler** (Programador de tareas):
   - Presiona `Win + R`
   - Escribe `taskschd.msc`
   - Presiona Enter

2. Haz clic en **"Create Basic Task"** (Crear tarea básica)

3. Configura la tarea:
   - **Name**: `Tennis Match Scraper`
   - **Description**: `Scrapes tennis matches every hour from live results`
   - Click **Next**

4. **Trigger** (Desencadenador):
   - Selecciona **Daily** (Diariamente)
   - Click **Next**
   - Start date: Hoy
   - Recur every: **1 days**
   - Click **Next**

5. **Action** (Acción):
   - Selecciona **Start a program** (Iniciar un programa)
   - Click **Next**
   - **Program/script**: `C:\Users\benja\OneDrive\Escritorio\Sistema Tenis\scrapers\run_scraper.bat`
   - Click **Next**

6. **Finish** (Finalizar):
   - Marca **"Open the Properties dialog"**
   - Click **Finish**

7. En **Properties** → **Triggers**:
   - Edita el trigger
   - Marca **"Repeat task every"**: `1 hour`
   - Duration: `Indefinitely`
   - Click **OK**

8. En **Properties** → **Settings**:
   - Marca **"Run task as soon as possible after a scheduled start is missed"**
   - Marca **"If the task fails, restart every"**: `5 minutes`, `3 times`
   - Click **OK**

### Paso 2: Probar la Tarea

Haz clic derecho en la tarea → **Run** para probarla manualmente.

## 📊 Qué Hace el Scraper

- **Fuente**: Scrapes de sitios de resultados de tenis en vivo
- **Frecuencia**: Cada hora automáticamente
- **Datos obtenidos**:
  - Partidos finalizados del día
  - Resultados (ganador, perdedor, score)
  - Torneo y superficie
  - Estadísticas detalladas (si disponibles)

- **Almacenamiento**: Inserta automáticamente en Supabase (tabla `matches`)
- **Deduplicación**: No inserta partidos duplicados

## ⚠️ Limitaciones Actuales

El scraper actual solo guarda partidos de jugadores que **ya están en tu base de datos** (los 848 jugadores que tienes).

### Para Obtener TODOS los Partidos

Necesito modificar el scraper para que guarde todos los partidos, no solo los de jugadores conocidos. ¿Quieres que haga este cambio?

## 🔧 Comandos Útiles

### Ejecutar scraper manualmente (una vez):
```bash
cd "C:\Users\benja\OneDrive\Escritorio\Sistema Tenis\scrapers"
python live_monitor.py --once
```

### Ver logs en tiempo real:
```bash
cd "C:\Users\benja\OneDrive\Escritorio\Sistema Tenis\scrapers"
python live_monitor.py
```

### Detener scraper:
Presiona `Ctrl+C`

## 📈 Próximos Pasos

1. ✅ Scraper configurado y funcionando
2. ⏳ Crear tarea en Task Scheduler (manual - sigue los pasos arriba)
3. ⏳ Modificar scraper para guardar TODOS los partidos (no solo jugadores conocidos)
4. ⏳ Agregar scraper de partidos programados (próximos días)
