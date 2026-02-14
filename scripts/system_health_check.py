import os
import sys
import requests
import warnings
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore")

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

def print_status(component, status, message=""):
    color = "\033[92m" if status == "OK" else ("\033[93m" if status == "WARN" else "\033[91m")
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] {component}: {message}")

def check_database():
    try:
        from scrapers.db_client import get_db_client
        db = get_db_client()
        if not db:
            print_status("Base de Datos", "FALLO", "No se pudo inicializar el cliente DB")
            return False
        
        # Simple query to check connectivity
        try:
            # Try to fetch 1 player to verify connection
            response = db.table('players').select('id').limit(1).execute()
            if hasattr(response, 'data'):
                print_status("Base de Datos", "OK", "Conexión exitosa (Query ejecutada)")
                return True
            else:
                 print_status("Base de Datos", "FALLO", f"Resultado de query inválido: {response}")
                 return False
        except Exception as e:
             print_status("Base de Datos", "FALLO", f"Query falló: {e}")
             return False

    except ImportError:
        print_status("Base de Datos", "FALLO", "No se pudo importar db_client")
        return False
    except Exception as e:
        print_status("Base de Datos", "FALLO", str(e))
        return False

def check_api():
    try:
        # Assuming API runs on localhost:8000
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print_status("API", "OK", "Backend funcionando")
            return True
        else:
            print_status("API", "WARN", f"Backend respondió con {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status("API", "WARN", "Backend no está corriendo (localhost:8000)")
        return False
    except Exception as e:
        print_status("API", "FALLO", str(e))
        return False

def check_scrapers():
    # Check if we can import key scrapers
    try:
        import scrapers.match_scraper
        import scrapers.live_monitor
        print_status("Scrapers", "OK", "Módulos cargados correctamente")
        return True
    except ImportError as e:
        print_status("Scrapers", "FALLO", f"Importación falló: {e}")
        return False

def check_ai_engine():
    try:
        from ai_engine.predict import StatsEngine
        # Just check if we can import and class exists
        if StatsEngine:
            print_status("Motor IA", "OK", "Módulo del motor cargado")
            return True
    except ImportError:
        print_status("Motor IA", "FALLO", "No se pudo importar StatsEngine")
        return False
    except Exception as e:
        print_status("Motor IA", "FALLO", str(e))
        return False

def check_disk_space():
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (2**30)
        if free_gb > 2:
            print_status("Sistema", "OK", f"Espacio en Disco OK ({free_gb}GB libres)")
        else:
            print_status("Sistema", "WARN", f"Poco Espacio en Disco ({free_gb}GB libres)")
    except Exception:
         print_status("Sistema", "WARN", "No se pudo verificar espacio en disco")

if __name__ == "__main__":
    print("\n=== DIAGNÓSTICO DEL SISTEMA ===\n")
    check_database()
    check_api()
    check_scrapers()
    check_ai_engine()
    check_disk_space()
    print("\n===============================\n")
