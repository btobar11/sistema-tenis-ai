from db_client import get_db_client
import json
import sys
import os

# Ensure we can import from local dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check():
    db = get_db_client()
    try:
        if not db:
            print("DB Connection Failed.")
            return

        # Check count of scheduled matches
        print("Checking 'scheduled' matches...")
        res = db.from_('matches').select('*').eq('status', 'scheduled').limit(5).execute()
        if res.error:
            print(f"Error querying matches: {res.error}")
        else:
            print(f"Found {len(res.data)} scheduled matches.")
            if res.data:
                print(json.dumps(res.data[0], indent=2, default=str))

        # Check recent inserts (any status)
        print("\nChecking recent matches (any status)...")
        res2 = db.from_('matches').select('*').order('date', desc=True).limit(5).execute()
        if res2.data:
            for m in res2.data:
                print(f"ID: {m.get('id')} | Date: {m.get('date')} | Status: {m.get('status')} | Tournament: {m.get('tournament_name')}")
        else:
            print("No matches found in DB at all (or query failed).")
        
    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    check()
