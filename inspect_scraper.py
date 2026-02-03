import sys
import os
sys.path.append(os.getcwd())

from scrapers.db_client import get_db_client

def inspect():
    print("--- Inspecting DB Content ---")
    db = get_db_client()
    
    # 1. Upcoming Matches
    res = db.from_('upcoming_matches').select('*').limit(3).execute()
    print(f"\n[Upcoming Matches] Data: {res.data}")
    if res.error: print(f"Error: {res.error}")
    
    # 2. Predictions
    res = db.from_('predictions').select('id, player1_name, player2_name, confidence, dq_score, engine_reason').limit(3).execute()
    # Note: scraping names are not in predictions table, only IDs. 
    # But for inspection let's just dump what we have or join? 
    # Actually predictions just has IDs. We'll just look at the scores.
    res = db.from_('predictions').select('confidence, dq_score, ss_score, engine_reason, surface').limit(5).order('created_at', desc=True).execute()
    
    print(f"\n[Latest Predictions] Data: {res.data}")
    if res.error: print(f"Error: {res.error}")

if __name__ == "__main__":
    inspect()
