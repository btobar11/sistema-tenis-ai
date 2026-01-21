from live_monitor import get_db_client, get_tracked_players, monitor_cycle
import os
import sys

# Ensure execution from the correct directory for relative imports/paths
# We assume this script is run from inside 'scrapers/' directory

def run_cron_cycle():
    print("--- Starting Scheduled Cron Job ---")
    
    # 1. Setup DB
    db = get_db_client()
    if not db:
        print("CRITICAL: No Database Connection. set SUPABASE_URL and SUPABASE_KEY.")
        sys.exit(1)
        
    # 2. Get Players
    tracked_players = get_tracked_players(db)
    print(f"Tracking {len(tracked_players)} players.")
    
    # 3. Run One Cycle (Scrape -> Save -> Trigger AI)
    # Note: monitor_cycle already contains the logic to call 'python ai_engine/predict.py'
    monitor_cycle(db, tracked_players)
    
    print("--- Cron Job Finished Successfully ---")

if __name__ == "__main__":
    run_cron_cycle()
