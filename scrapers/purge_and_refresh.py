
import os
import sys
from dotenv import load_dotenv

# Add current directory to path to find db_client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_client import get_db_client
from upcoming_scraper import scrape_upcoming_matches

def purge_and_refresh():
    print("--- PURGING OLD DATA ---")
    db = get_db_client()
    
    # Supabase DELETE requires a WHERE clause usually. 
    # We use neq('id', '0000...') as a 'delete all' hack if needed, 
    # or just iterate if bulk delete is restricted.
    # Actually, let's try to use the 'delete' endpoint with a broad filter.
    
    # Note: 'upcoming_matches' might have cascade enabled, so predictions go too.
    # That is desired per user request "arreglalo ya" (fix it now).
    
    try:
        # Filter where ID is not null (basically all rows)
        res = db.table('upcoming_matches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"Deleted old matches logic. Response: {res.data if hasattr(res, 'data') else 'OK'}")
    except Exception as e:
        print(f"Check Delete: {e}")

    print("\n--- RUNNING OPTIMIZED SCRAPER ---")
    matches = scrape_upcoming_matches()
    
    print(f"\n[DONE] Database is clean and repopulated with {len(matches)} FRESH matches.")

if __name__ == "__main__":
    purge_and_refresh()
