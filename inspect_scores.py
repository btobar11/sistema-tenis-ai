import os
import sys
sys.path.append(os.getcwd())
from scrapers.db_client import get_db_client

def inspect():
    supabase = get_db_client()
    # Select score_full (and potentially winner_id to check)
    res = supabase.table('matches').select('score_full, tournament_name, id').limit(10).execute()
    
    print("Found matches:", len(res.data))
    for m in res.data:
        print(f"Match {m['id']} | Score: {m.get('score_full')} | Tourney: {m.get('tournament_name')}")

if __name__ == "__main__":
    inspect()
