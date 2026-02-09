import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_client import get_db_client
import json

def inspect_finished():
    db = get_db_client()
    # Fetch finished matches
    r = db.from_('matches').select('*').eq('status', 'finished').limit(10).execute()
    found = False
    if r.data:
        for m in r.data:
            if m.get('stats_json'):
                print(f"Match: {m['id']} | Score: {m.get('score')}")
                print("Stats JSON Keys:", m.get('stats_json', {}).keys())
                print(json.dumps(m.get('stats_json'), indent=2))
                found = True
                break
    
    if not found:
        print("No finished matches with stats found.")

if __name__ == "__main__":
    inspect_finished()
