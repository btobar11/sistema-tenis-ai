from live_monitor import get_db_client, get_tracked_players, monitor_cycle
import os
import sys
import argparse

# Ensure execution from the correct directory for relative imports/paths
# We assume this script is run from inside 'scrapers/' directory

def run_cron_cycle(mode='all'):
    print(f"--- Starting Scheduled Cron Job (Mode: {mode}) ---")
    
    # 1. Setup DB
    db = get_db_client()
    if not db:
        print("CRITICAL: No Database Connection. set SUPABASE_URL and SUPABASE_KEY.")
        sys.exit(1)
        
    # 2. Live Monitor (Updates Scores, ELO, & Trigger AI)
    if mode in ['all', 'live']:
        print("\n[Cron] Starting Live Monitor Cycle...")
        try:
            tracked_players = get_tracked_players(db)
            print(f"Tracking {len(tracked_players)} players.")
            # monitor_cycle already contains the logic to call 'python ai_engine/predict.py'
            monitor_cycle(db, tracked_players)
        except Exception as e:
            print(f"[Cron] Live Monitor Failed: {e}")

    # 3. Update Upcoming Matches
    if mode in ['all', 'upcoming']:
        print("\n[Cron] Updating Upcoming Matches...")
        try:
            from upcoming_scraper import run_upcoming_scraper
            run_upcoming_scraper()
        except Exception as e:
            print(f"[Cron] Upcoming Scraper Failed: {e}")

    # 4. Run Value Bet Analysis (Real Odds)
    if mode in ['all', 'value']:
        print("\n[Cron] Finding Value Bets...")
        try:
            # Hack path to ensure we can import from parent 'metrics'
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from metrics.value import ValueBetEngine
            engine = ValueBetEngine(db)
            engine.process_value_bets()
        except Exception as e:
            print(f"[Cron] Value Bet Engine Failed: {e}")
    
    print("--- Cron Job Finished Successfully ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Tennis AI Cron Jobs')
    parser.add_argument('--mode', type=str, default='all', choices=['all', 'live', 'upcoming', 'value'],
                        help='Which part of the pipeline to run')
    args = parser.parse_args()
    
    run_cron_cycle(mode=args.mode)
