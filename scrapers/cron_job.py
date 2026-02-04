from live_monitor import get_db_client, get_tracked_players, monitor_cycle
import os
import sys
import argparse

# Ensure execution from the correct directory for relative imports/paths
# We assume this script is run from inside 'scrapers/' directory

import traceback

def run_cron_cycle(mode='all'):
    print(f"--- Starting Scheduled Cron Job (Mode: {mode}) ---")
    
    # Ensure root path is known for absolute imports from siblings
    # If running from scrapers/cron_job.py, the root is one level up.
    # If running from root as python scrapers/cron_job.py, we still want to be sure.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 1. Setup DB
    try:
        db = get_db_client()
        if not db:
            raise Exception("Failed to initialize Database Client")
    except Exception as e:
        print("CRITICAL: Database Connection Failed.")
        traceback.print_exc()
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
            print(f"[Cron] Live Monitor Failed:")
            traceback.print_exc()

    # 3. Update Upcoming Matches
    if mode in ['all', 'upcoming']:
        print("\n[Cron] Updating Upcoming Matches...")
        try:
            from scrapers.upcoming_scraper import run_upcoming_scraper
            run_upcoming_scraper()
        except ImportError:
            # Fallback if running from inside scrapers dir without package context? 
            try:
                from upcoming_scraper import run_upcoming_scraper
                run_upcoming_scraper()
            except Exception as e:
                 print(f"[Cron] Upcoming Scraper Import Failed: {e}")
        except Exception as e:
            print(f"[Cron] Upcoming Scraper Failed:")
            traceback.print_exc()

    # 4. Run Value Bet Analysis (Real Odds)
    if mode in ['all', 'value']:
        print("\n[Cron] Finding Value Bets...")
        try:
            from metrics.value import ValueBetEngine
            engine = ValueBetEngine(db)
            engine.process_value_bets()
        except Exception as e:
            print(f"[Cron] Value Bet Engine Failed:")
            traceback.print_exc()
    
    print("--- Cron Job Finished Successfully ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Tennis AI Cron Jobs')
    parser.add_argument('--mode', type=str, default='all', choices=['all', 'live', 'upcoming', 'value'],
                        help='Which part of the pipeline to run')
    args = parser.parse_args()
    
    run_cron_cycle(mode=args.mode)
