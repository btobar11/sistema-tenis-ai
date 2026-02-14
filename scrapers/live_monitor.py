import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import requests as http_requests # Standard requests for API
import sys
import argparse
# Add parent directory to path to allow importing 'metrics' and 'ai_engine'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime, timedelta
from db_client import get_db_client, get_or_create_player
from match_scraper import scrape_today_results, scrape_match_details
from stats_utils import scrape_detailed_stats, save_stats

# Load env from parent or current dir
load_dotenv()

from db_client import get_db_client

# SUPABASE_URL and KEY are handled in db_client


def get_tracked_players(db):
    if not db:
        # Mock for detailed testing if no DB
        return {"carlos alcaraz", "jannik sinner", "rafael nadal", "novak djokovic", "jeanne-grandinot d."} 
    # Fetch players from DB
    try:
        # Assuming we just want all players in DB? Or a specific list?
        # For now, let's fetch top 100 or all.
        r = db._request_with_retry('get', f"{db.url}/rest/v1/players?select=name&limit=1000")
        if r and r.status_code == 200:
            players = r.json()
            return {p['name'].lower() for p in players if p.get('name')}
        return set()
    except Exception as e:
        print(f"Error fetching tracked players: {e}")
        return set()

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
    
    # Initialize Metrics Engines
    try:
        from metrics.elo import EloEngine
        elo_engine = EloEngine(db)
    except ImportError:
        elo_engine = None
        print("  [Warning] EloEngine not found or failed to load.")

    new_matches_count = 0
    
    for m in matches:
        print(f"  -> Processing: {m['winner']} vs {m['loser']}")
        
        p1_id = None
        p2_id = None

        if db:
            p1_id = db.get_or_create_player(m['winner'])
            p2_id = db.get_or_create_player(m['loser'])
            
            if not p1_id or not p2_id:
                continue
                
            # Optimization: Check if match already exists and is finished
            try:
                # Basic date string for query
                # Basic date string for query
                base_date = m['date'][:10]
                day_start = base_date + "T00:00:00"
                day_end = base_date + "T23:59:59"

                # Robust check for (p1, p2) OR (p2, p1)
                existing = db.table('matches')\
                    .select('id, status, player1_id, player2_id')\
                    .gte('date', day_start)\
                    .lte('date', day_end)\
                    .or_(f"player1_id.eq.{p1_id},player2_id.eq.{p1_id}")\
                    .execute()
                
                if existing.data:
                    # Filter in python to be sure (since OR query checks if EITHER matches p1_id)
                    # We need (p1=A AND p2=B) OR (p1=B AND p2=A)
                    # The query `.or_(f"player1_id.eq.{p1_id},player2_id.eq.{p1_id}")` returns matches where P1 is A OR P2 is A.
                    # We then need to check if the OTHER player is B.
                    found_match = None
                    for em in existing.data:
                        if (em['player1_id'] == p1_id and em['player2_id'] == p2_id) or \
                           (em['player1_id'] == p2_id and em['player2_id'] == p1_id):
                            found_match = em
                            break
                    
                    if found_match and found_match.get('status') == 'finished':
                         print(f"     [SKIP] Already finished in DB (ID: {found_match['id']})")
                         
                         # Check if we have stats for this finished match
                         # This is a good place to double check if stats were missed
                         if m.get('detail_url'):
                             # Quick check or just re-scrape to be safe? 
                             # Let's simple scrape and save (idempotent)
                             print(f"     [STATS] Ensuring stats for existing match...")
                             stats = scrape_detailed_stats(m['detail_url'])
                             if stats:
                                 if found_match['player1_id'] == p1_id:
                                      save_stats(db, found_match['id'], p1_id, stats['p1'])
                                      save_stats(db, found_match['id'], p2_id, stats['p2'])
                                 else:
                                      # Swap
                                      save_stats(db, found_match['id'], found_match['player1_id'], stats['p2'])
                                      save_stats(db, found_match['id'], found_match['player2_id'], stats['p1'])
                         
                         continue
            except Exception as check_e:
                print(f"     [WARN] Check existing failed: {check_e}")

        else:
            p1_id = "DRY_RUN_ID"
            p2_id = "DRY_RUN_ID"
        
        # Fetch details if available (and not skipped)
        details = {}
        if m['detail_url']:
             details = scrape_match_details(m['detail_url'])
             time.sleep(2.0) # Delay to respect rate limits
        
        # Resolve IDs (Redundant if db check passed, but safe)
        # We already have p1_id, p2_id if db is present
            
        # Try to infer surface from tournament name
        surface = "hard"
        t_name_upper = m['tournament'].upper()
        if "CLAY" in t_name_upper: surface = "clay"
        elif "GRASS" in t_name_upper: surface = "grass"
        elif "INDOOR" in t_name_upper: surface = "hard" # Map indoor to hard 
        
        # Prepare DB Payload
        match_date = m['date']
        if len(match_date) == 10: 
             match_date += "T00:00:00+00:00"

        db_match = {
            "date": match_date, 
            "tournament_name": m['tournament'],
            "surface": surface,
            "player1_id": p1_id, 
            "player2_id": p2_id,
            "winner_id": p1_id, 
            "winner_name": m['winner'], 
            "status": "finished", 
            "score_full": m['score'],
            "stats_json": details, 
        }
        
        # Save to DB
        if db:
                match_id = db.insert_match(db_match)
                
                # Check for Detailed Stats (Live or Finished)
                if m.get('detail_url'): # Use m (scraped data) here
                    # Only scrape stats if status is finished or set 1+ completed to avoid too much traffic?
                    # TennisExplorer stats appear usually when match is live too.
                    print(f"     [STATS] Scraping deep stats for {db_match['winner_name']} vs {m['loser']}...")
                    stats = scrape_detailed_stats(m['detail_url'])
                    if stats and match_id:
                         save_stats(db, match_id, p1_id, stats['p1'])
                         save_stats(db, match_id, p2_id, stats['p2'])
                
                if match_id:
                    print(f"     [OK] Saved/Updated: {db_match['winner_name']} vs {m['loser']}")
                new_matches_count += 1
                
                # Update ELO Immediately
                if elo_engine:
                    print(f"     [ELO] Updating ratings...")
                    elo_engine.process_match(db_match)
        else:
            print(f"     [DRY RUN] Would save: {db_match['score']}")
    
    # Moved OUTSIDE the loop
    print(f"  Cycle finished. {new_matches_count} new matches saved.")
    
    if new_matches_count > 0:
        # Trigger Prediction Engine only if new data arrived
        print("  [AI] Triggering Prediction Engine...")
        try:
            import sys
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                
            from ai_engine.predict import predict_matches
            predict_matches()
            
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single monitor cycle and exit")
    args = parser.parse_args()

    if args.once:
        print(f"[{datetime.now()}] Running in ONCE mode.")
        db = get_db_client()
        tracked = get_tracked_players(db)
        monitor_cycle(db, tracked)
        print("Single cycle completed.")
    else:
        run_continuous_monitor()
