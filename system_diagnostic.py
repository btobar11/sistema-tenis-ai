import os
import sys
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db_client import get_db_client
from scrapers.match_scraper import scrape_today_results
from ai_engine.predict import StatsEngine

load_dotenv()

def check_db():
    print("1. [DB CHECK]")
    db = get_db_client()
    if not db:
        print("   [FAIL] Could not initialize DB client.")
        return False
    
    # Check tables via direct query (or just check if we can select)
    try:
        # Check players
        r = db._request_with_retry('get', f"{db.url}/rest/v1/players?select=count", headers={"Range": "0-0"})
        if r.status_code in [200, 206]:
            print(f"   [PASS] Players table accessible. (Range query status: {r.status_code})")
        else:
            print(f"   [FAIL] Players table error: {r.status_code} {r.text}")

        # Check matches and prediction column
        r2 = db._request_with_retry('get', f"{db.url}/rest/v1/matches?select=prediction&limit=1")
        if r2.status_code == 200:
             print("   [PASS] Matches table accessible.")
             # Check if we got data or empty list, implies schema is OK if 200
             print("   [PASS] 'prediction' column exists (query successful).")
        else:
             print(f"   [FAIL] Matches table/schema error: {r2.status_code} {r2.text}")
             
    except Exception as e:
        print(f"   [FAIL] DB connection exception: {e}")
        return False
    return True

def check_scrapers():
    print("\n2. [SCRAPER CHECK]")
    try:
        # Dry run match scraper
        print("   Running match_scraper (dry run)...")
        matches = scrape_today_results() # This prints to stdout, might be noisy
        if isinstance(matches, list):
            print(f"   [PASS] match_scraper returned {len(matches)} matches.")
            if len(matches) > 0:
                 print(f"   Sample: {matches[0]['winner']} vs {matches[0]['loser']}")
        else:
            print("   [FAIL] match_scraper returned invalid type.")
            
    except Exception as e:
         print(f"   [FAIL] Scraper validation failed: {e}")

def check_ai_integration():
    print("\n3. [AI ENGINE CHECK]")
    try:
        db = get_db_client()
        if not db: 
            print("   [SKIP] No DB for AI check.")
            return

        engine = StatsEngine(db)
        # Mock match data
        mock_match = {
            'player1_id': 'mock_p1',
            'player2_id': 'mock_p2'
        }
        # We can't easily run predict_match because it queries DB for H2H using IDs.
        # But we can check if class instantiates and basic methods exist.
        if hasattr(engine, 'predict_match'):
             print("   [PASS] StatsEngine initialized correctly.")
        
        # Check if we can fetch recent form for value 0 (should return empty stats structure)
        stats = engine.get_player_recent_form('00000000-0000-0000-0000-000000000000')
        if stats and 'win_rate' in stats:
             print("   [PASS] StatsEngine.get_player_recent_form handled empty/invalid ID gracefully.")
        else:
             print("   [FAIL] StatsEngine.get_player_recent_form failed structure check.")

    except Exception as e:
        print(f"   [FAIL] AI Engine check failed: {e}")

if __name__ == "__main__":
    print("=== SYSTEM DIAGNOSTIC START ===")
    check_db()
    check_scrapers()
    check_ai_integration()
    print("=== SYSTEM DIAGNOSTIC END ===")
