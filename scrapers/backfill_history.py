import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests as http_requests
from match_scraper import scrape_today_results
from db_client import get_db_client

load_dotenv()

def backfill_history(days=180):
    print(f"Starting backfill for last {days} days...")
    
    db = get_db_client()
    if not db:
        print("Error: Supabase credentials missing (check .env)")
        return
    
    start_date = datetime.now() - timedelta(days=1)
    
    for i in range(days):
        target_date = start_date - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"[{i+1}/{days}] Scraping {date_str}...")
        
        matches = scrape_today_results(target_date)
        print(f"  Found {len(matches)} raw matches")
        
        saved = 0
        for m in matches:
            # Resolve IDs
            p1_id = db.get_or_create_player(m['winner'])
            p2_id = db.get_or_create_player(m['loser'])
            
            if not p1_id or not p2_id:
                # print(f"  Skipping match {m['winner']} vs {m['loser']} (ID fail)")
                continue
                
            db_match = {
                "tournament_name": m['tournament'],
                # "surface": "Hard", # Scraper doesn't get surface yet?
                # "round": "F", 
                "date": m['date'],
                "player1_id": p1_id,
                "player2_id": p2_id,
                "winner_id": p1_id, 
                "score_full": m['score'],
                "stats_json": {}, # Populate if we want to scrape details
                # "status": "finished"
            }
            
            # Use shared client insert (handles generic duplicate check)
            if db.insert_match(db_match):
                saved += 1
                print(f"    Saved: {m['winner']} d. {m['loser']}")
        
        print(f"  Saved {saved} new matches from {date_str}")
        time.sleep(1) 

if __name__ == "__main__":
    # careful with defaults
    print("WARNING: This will backfill data. Press Enter to continue 180 days check...")
    # input() 
    backfill_history(30) # Default to 30 days for test safety

