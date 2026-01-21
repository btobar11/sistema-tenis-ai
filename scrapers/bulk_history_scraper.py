import os
import sys
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from match_scraper import scrape_today_results

# Load env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal" # Don't need response body for inserts
}

# Cache for player IDs to avoid 2 calls per match
PLAYER_CACHE = {}

def get_or_create_player(name):
    if name in PLAYER_CACHE:
        return PLAYER_CACHE[name]
        
    # Try to find player
    url = f"{SUPABASE_URL}/rest/v1/players?name=eq.{name}&select=id"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200 and r.json():
        pid = r.json()[0]['id']
        PLAYER_CACHE[name] = pid
        return pid
        
    # Create player
    payload = {"name": name, "plays_hand": "U", "country": "UNK"} 
    
    headers_upsert = HEADERS.copy()
    headers_upsert["Prefer"] = "return=representation,resolution=merge-duplicates"
    
    r = requests.post(f"{SUPABASE_URL}/rest/v1/players", headers=headers_upsert, json=payload)
    if r.status_code in [200, 201] and r.json():
        pid = r.json()[0]['id']
        PLAYER_CACHE[name] = pid
        return pid
    else:
        print(f"    Error creating player {name}: {r.text[:100]}")
        return None

def bulk_scrape(days_back=14):
    print(f"Starting bulk scrape for last {days_back} days...")
    
    total_matches_saved = 0
    start_date = datetime.now()
    
    for i in range(days_back):
        target_date = start_date - timedelta(days=i)
        print(f"[{i+1}/{days_back}] Scraping {target_date.strftime('%Y-%m-%d')}...")
        
        try:
            matches = scrape_today_results(target_date)
            print(f"  Found {len(matches)} matches.")
            
            if not matches:
                continue
                
            for m in matches:
                # 1. Resolve Players
                p1_name = m['winner'].strip()
                p2_name = m['loser'].strip()
                
                p1_id = get_or_create_player(p1_name)
                p2_id = get_or_create_player(p2_name)
                
                if not p1_id or not p2_id:
                    print(f"    Skipping match {p1_name} vs {p2_name} (ID missing)")
                    continue
                
                # 2. Insert Match
                # Schema: id, tournament_name, date, surface, player1_id, player2_id, winner_id, score_full, stats_json
                
                # Heuristic for Surface
                t_lower = m['tournament'].lower()
                surface = 'Hard'
                if 'clay' in t_lower or 'garros' in t_lower or 'rome' in t_lower or 'madrid' in t_lower:
                    surface = 'Clay'
                elif 'grass' in t_lower or 'wimbledon' in t_lower or 'halle' in t_lower:
                    surface = 'Grass'
                
                db_match = {
                    "tournament_name": m['tournament'],
                    "date": m['date'], # YYYY-MM-DD. Timestamp? Postgres handles casting usually.
                    "surface": surface,
                    "player1_id": p1_id, # We put Winner as P1 here for simplicity? 
                                         # Or better: P1 is just P1. We set winner_id below.
                    "player2_id": p2_id,
                    "winner_id": p1_id,
                    "score_full": m['score'],
                    "stats_json": {} # Empty for now
                }
                
                # Upsert match? Based on Players + Date?
                # matches usually doesn't have unique constraint on players+date (could play twice? rare).
                # But let's just insert.
                
                url = f"{SUPABASE_URL}/rest/v1/matches"
                r = requests.post(url, headers=HEADERS, json=db_match)
                if r.status_code == 201:
                    total_matches_saved += 1
                else:
                    # Duplicate or error
                    pass # print(f"    Error saving match: {r.text[:50]}")
                    
            print(f"  Processed {len(matches)} matches.")
            
        except Exception as e:
            print(f"  Error processing date: {e}")
            
        time.sleep(1) 
        
    print(f"Bulk scrape finished. Total saved: {total_matches_saved}")

if __name__ == "__main__":
    # Scrape last 14 days to get good history
    bulk_scrape(14)
