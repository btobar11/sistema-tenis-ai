import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import requests as http_requests # Standard requests for API
from match_scraper import scrape_today_results, scrape_match_details

# Load env from parent or current dir
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseRestClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_tracked_players(self):
        # GET /rest/v1/players?select=name
        endpoint = f"{self.url}/rest/v1/players?select=name"
        try:
            r = http_requests.get(endpoint, headers=self.headers)
            if r.status_code == 200:
                return {row['name'].lower() for row in r.json()}
            print(f"DB Error: {r.text}")
        except Exception as e:
            print(f"DB Connection Error: {e}")
        return set()

    def insert_match(self, match_data):
        # POST /rest/v1/matches
        endpoint = f"{self.url}/rest/v1/matches"
        try:
            # Check if match already exists (by winner, loser, date, tournament)
            check_endpoint = f"{self.url}/rest/v1/matches?winner_name=eq.{match_data.get('winner_name')}&loser_name=eq.{match_data.get('loser_name')}&tournament_name=eq.{match_data.get('tournament')}&select=id"
            check_response = http_requests.get(check_endpoint, headers=self.headers)
            
            if check_response.status_code == 200 and len(check_response.json()) > 0:
                # Match already exists, skip
                return False
            
            # Insert new match
            r = http_requests.post(endpoint, headers=self.headers, json=match_data)
            if r.status_code in [200, 201]:
                return True
            print(f"DB Insert Error: {r.text}")
        except Exception as e:
            print(f"DB Insert Failed: {e}")
        return False

def get_db_client():
    if SUPABASE_URL and SUPABASE_KEY:
        return SupabaseRestClient(SUPABASE_URL, SUPABASE_KEY)
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set. Running in DRY RUN mode.")
    return None

def get_tracked_players(db):
    if not db:
        # Mock for detailed testing if no DB
        return {"carlos alcaraz", "jannik sinner", "rafael nadal", "novak djokovic", "jeanne-grandinot d."} 
    return db.get_tracked_players()

def normalize_name(name):
    # TennisExplorer: "Sinner J." or "Alcaraz C."
    # DB: "Jannik Sinner" or "Carlos Alcaraz"
    # We need fuzzy matching or "Lastname Firstname" check.
    # TE format is usually "Lastname Initial."
    # We will try to match "Lastname" in DB.
    
    # Robust logic: Split DB name "Carlos Alcaraz" -> "Alcaraz"
    # TE Name "Alcaraz C." -> "Alcaraz"
    # Match on Lastname? Risk of collision (e.g. Zverev A. vs Zverev M.)
    
    # For now, simplified lower case mapping
    # return name.lower().split(' ')[0] 
    return name.lower()

def match_player_name(te_name, db_players_set):
    """
    Tries to find te_name (e.g. 'Nadal R.') in db_players_set (e.g. 'rafael nadal')
    """
    # TE: "Nadal R." -> base "nadal"
    te_base = te_name.split(' ')[0].lower()
    
    # Simple check: is 'base' in any db name?
    # This is O(N) per match, fine for 800 players.
    for db_p in db_players_set:
        if te_base in db_p:
            # Check initial?
            # Nadal R. vs Rafael Nadal -> 'r' matches 'rafael'
            parts = te_name.split(' ')
            if len(parts) > 1:
                initial = parts[1][0].lower()
                # Check if first name starts with initial
                # db_p format: "Firstname Lastname" usually?
                # Actually, my DB has "Novak Djokovic". Lastname is last.
                db_parts = db_p.split(' ')
                db_last = db_parts[-1]
                db_first = db_parts[0]
                
                if db_last == te_base and db_first.startswith(initial):
                    return db_p # Return full DB name
            elif te_base in db_p: 
                 return db_p
                 
    return None

def monitor_cycle(db, tracked_players):
    print(f"[{datetime.now()}] Checking for new results...")
    
    # Scrape Today's Matches
    matches = scrape_today_results()
    print(f"  Scraped {len(matches)} matches from source.")
    
    new_matches_count = 0
    
    for m in matches:
        # SAVE ALL MATCHES - No longer filtering by tracked players
        # winner_db_name = match_player_name(m['winner'], tracked_players)
        # loser_db_name = match_player_name(m['loser'], tracked_players)
        
        # if winner_db_name or loser_db_name:  # REMOVED - Save all matches now
        
        print(f"  -> Processing: {m['winner']} vs {m['loser']}")
        
        # Fetch details if available
        details = {}
        if m['detail_url']:
             details = scrape_match_details(m['detail_url'])
             time.sleep(0.5) 
        
        # Prepare DB Payload
        db_match = {
            "match_date": m['date'],
            "tournament": m['tournament'],
            "winner_name": m['winner'], 
            "loser_name": m['loser'],
            "score": m['score'],
            "stats_json": details, 
        }
        
        # Save to DB
        if db:
            success = db.insert_match(db_match)
            if success:
                print(f"     [SAVED] {db_match['winner_name']} d. {db_match['loser_name']}")
                new_matches_count += 1
        else:
            print(f"     [DRY RUN] Would save: {db_match['score']}")
    
    if new_matches_count > 0:
        print(f"  Cycle finished. {new_matches_count} new matches saved.")
        # Trigger Prediction Engine
        print("  [AI] Triggering Prediction Engine...")
        try:
            # Using python directly. Assumes internal relative path or same venv.
            # current dir is scrapers/
            os.system("python ai_engine/predict.py")
        except Exception as e:
            print(f"  [AI Error] Could not run prediction: {e}")
    else:
        print("  Cycle finished. No new matches found.")

def run_continuous_monitor(interval_seconds=600):
    print(f"[{datetime.now()}] Starting Continuous Live Monitor (Interval: {interval_seconds}s)...")
    db = get_db_client()
    
    # Refresh tracked players once or periodically? 
    # Let's refresh every cycle to pick up new signups/additions?
    # Or maybe once an hour. For simplicity, every cycle (it's one query).
    
    while True:
        try:
            # Refresh players list in case DB changed
            tracked_players = get_tracked_players(db)
            if not tracked_players:
               print("  Warning: No players to track (or DB error).")
            
            monitor_cycle(db, tracked_players)
            
        except Exception as e:
            print(f"  [CRITICAL ERROR] Monitor cycle crashed: {e}")
        
        print(f"  Sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_continuous_monitor()
