import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import requests as http_requests # Standard requests for API
from match_scraper import scrape_today_results, scrape_match_details

# Load env from parent or current dir
load_dotenv()

from db_client import get_db_client

# SUPABASE_URL and KEY are handled in db_client


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
        
        # Fetch details if available
        details = {}
        if m['detail_url']:
             details = scrape_match_details(m['detail_url'])
             time.sleep(0.5) 
        
        # Resolve IDs
        if db:
            p1_id = db.get_or_create_player(m['winner'])
            p2_id = db.get_or_create_player(m['loser'])
            
            if not p1_id or not p2_id:
                continue
        else:
            p1_id = "DRY_RUN_ID"
            p2_id = "DRY_RUN_ID"

        # Prepare DB Payload
        db_match = {
            "date": m['date'], 
            "tournament_name": m['tournament'],
            "player1_id": p1_id, 
            "player2_id": p2_id,
            "winner_id": p1_id, # Scraper returns 'winner' name
            "score_full": m['score'],
            "stats_json": details, 
        }
        
        # Save to DB
        if db:
            success = db.insert_match(db_match)
            if success:
                print(f"     [SAVED] {db_match['winner_id']} vs {db_match['player2_id']}")
                new_matches_count += 1
                
                # Update ELO Immediately
                if elo_engine:
                    print(f"     [ELO] Updating ratings...")
                    # We pass the match dict. Ensure it has what process_match needs.
                    # process_match needs: player1_id, player2_id, winner_id
                    elo_engine.process_match(db_match)
        else:
            print(f"     [DRY RUN] Would save: {db_match['score']}")
    
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
                    
                from ai_engine.predict import predict_upcoming_matches
                predict_upcoming_matches()
                
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
