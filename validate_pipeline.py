
import sys
import os
import json
from datetime import datetime

# Add root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from scrapers.db_client import get_db_client
except ImportError:
    from db_client import get_db_client

def validate_data():
    db = get_db_client()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"--- VALIDATING DATA PIPELINE FOR {today} ---")
    
    # 1. Check Raw Scraper Output (via DB)
    print("\n[1] Checking Database Records:")
    res = db.from_('matches').select('*').gte('date', today + "T00:00:00").order('date', desc=True).limit(5).execute()
    
    if not res.data:
        print("❌ NO MATCHES FOUND in DB for today. Scraper might be failing.")
        return

    print(f"✅ Found {len(res.data)} matches for today.")
    
    valid_count = 0
    issues = []
    
    for m in res.data:
        # Check critical fields
        is_valid = True
        missing = []
        if not m.get('tournament_name'): missing.append('tournament_name')
        if not m.get('player1_id'): missing.append('player1_id')
        if not m.get('player2_id'): missing.append('player2_id')
        
        # specific check for status
        status = m.get('status')
        if status not in ['finished', 'live', 'scheduled']:
            missing.append(f"invalid_status({status})")

        if missing:
            is_valid = False
            issues.append(f"Match {m.get('id')}: Missing {','.join(missing)}")
        else:
            valid_count += 1
            
        # Print sample for user to see 'correctness'
        print(f"  -> ID: {m.get('id')[:8]}... | Date: '{m.get('date')}' | {m.get('winner_name') or 'TBD'} vs {m.get('loser') or 'TBD'}")

    if issues:
        print(f"\n⚠️ DATA QUALITY WARNINGS ({len(issues)}):")
        for i in issues: print(f"  - {i}")
    else:
        print("\n✅ Data Quality Looks Good (Schema matches expectations).")

if __name__ == "__main__":
    validate_data()
