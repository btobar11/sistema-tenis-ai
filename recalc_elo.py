import os
import sys
from dotenv import load_dotenv

# Ensure root path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scrapers.db_client import get_db_client
from metrics.elo import EloEngine

load_dotenv()

def recalc_history():
    print("Starting ELO Recalculation from History...")
    
    db = get_db_client()
    if not db:
        print("DB Failed")
        return
    
    engine = EloEngine(db)
    
    # Reset all ELOs? Or just process?
    # For a perfect backfill, we should ideally wipe elo_ratings or handle it carefully.
    # Assuming we want to process all matches in date order.
    
    # 1. Fetch all matches ordered by date ASC
    print("Fetching all matches...")
    # Pagination might be needed if thousands of matches.
    # For now, let's fetch last 1000 or so.
    endpoint = f"{db.url}/rest/v1/matches?select=*&order=date.asc&winner_id=not.is.null"
    
    r = db._request_with_retry('get', endpoint)
    if not r or r.status_code != 200:
        print("Failed to fetch matches")
        return
        
    matches = r.json()
    print(f"Processing {len(matches)} matches...")
    
    for i, m in enumerate(matches):
        if i % 50 == 0:
            print(f"  Processing {i}/{len(matches)}...")
        engine.process_match(m)
        
    print("ELO Recalculation Complete.")

if __name__ == "__main__":
    recalc_history()
