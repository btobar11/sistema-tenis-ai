# Sistema Tenis - Data Scrapers

Este directorio contiene los scripts de Python para la ingesta de datos automática.

## Configuración

1.  Crear entorno virtual:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate # Mac/Linux
    ```

2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

3.  Variables de Entorno:
    Crear un archivo `.env` en esta carpeta con:
    ```
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_service_role_key
    ```
    *Nota: Usar la `SERVICE_ROLE_KEY` para tener permisos de escritura sin restricciones.*

## Scripts

-   `players_scraper.py`: Obtiene el ranking ATP/WTA actual.
-   `setup.py`: Inicializa tablas o datos maestros si es necesario.
