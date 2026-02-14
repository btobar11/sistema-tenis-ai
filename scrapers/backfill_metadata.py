
import os
import sys
import requests
import re
from datetime import datetime
from dotenv import load_dotenv

# Add root directory to sys.path to allow imports from scrapers module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.db_client import get_db_client


load_dotenv()
db = get_db_client()

def backfill_metadata():
    print("--- Backfilling Metadata (Rankings & AI) ---")
    
    # 1. Backfill Rankings
    print("\n[1/2] Backfilling Rankings from Match Names...")
    # Fetch recent matches
    res = db.from_('matches').select('id, winner_name, loser_name, player1_id, player2_id').order('date', desc=True).limit(50).execute()
    matches = res.data or []
    
    updated_ranks = 0
    for m in matches:
        for name, pid in [(m['winner_name'], m['player1_id']), (m['winner_name'], m['player2_id']), # Check winner against P1/P2
                          (m['loser_name'], m['player1_id']), (m['loser_name'], m['player2_id'])]:   # Check loser against P1/P2
            
            # Simple heuristic: if name matches logic
            # Actually, scrape usually puts winner_name/loser_name with rank
            # We need to map which name string belongs to which ID
            
            if not name or not pid: continue
            
            # Extract rank
            match = re.search(r'\s*\((\d+)\)$', name)
            if match:
                rank = int(match.group(1))
                # Update player
                try:
                    db.from_('players').update({'rank_single': rank}).eq('id', pid).execute()
                    updated_ranks += 1
                except: pass

    print(f"Updated {updated_ranks} player rankings.")

    # 2. Trigger AI Analysis
    print("\n[2/2] Triggering AI Prediction for matches (Last 7 Days)...")
    try:
        from scrapers.ai_engine.predict import predict_matches
        from datetime import timedelta
        
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        # Pass status_filter=None to process ALL matches (scheduled, finished, etc.)
        predict_matches(start_date=start_date, status_filter=None)
        
    except Exception as e:
        print(f"AI Prediction Error: {e}")
        
    print("\nDone.")

if __name__ == "__main__":
    backfill_metadata()
