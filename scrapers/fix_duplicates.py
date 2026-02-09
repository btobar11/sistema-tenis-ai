import os
import requests
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print("--- FIXING DUPLICATES ---")

# 1. Fetch all matches for dates >= today (approx) to cover recent dupes
today = datetime.now().strftime("%Y-%m-%d")
resp = requests.get(f"{url}/rest/v1/matches?select=*&order=date.desc&limit=1000", headers=headers)

if resp.status_code != 200:
    print("Error fetching")
    exit()

matches = resp.json()
print(f"Fetched {len(matches)} matches.")

# Group by players and date (ignoring time)
groups = defaultdict(list)

for m in matches:
    # Key: P1_ID-P2_ID-DATE(YYYY-MM-DD)
    # Ensure ordered P1-P2 to catch A vs B and B vs A duplication if any (though IDs usually stable)
    p1 = m['player1_id']
    p2 = m['player2_id']
    
    # Sort IDs to be independent of P1/P2 order if duplicates are reversed
    ids = sorted([str(p1), str(p2)])
    date_str = m['date'].split('T')[0]
    
    group_key = f"{ids[0]}-{ids[1]}-{date_str}"
    groups[group_key].append(m)

deleted_count = 0
for key, group in groups.items():
    if len(group) > 1:
        print(f"Found duplicate group: {key} ({len(group)} records)")
        
        # Decide which to keep
        # Prefer: status='finished', or has winner_name, or has score
        # Sort group: Finished > Not Finished, Score len > 0
        
        def score_val(x):
            s = x.get('score_full') or ""
            return len(s)
            
        def status_val(x):
            return 1 if x.get('status') == 'finished' else 0
            
        # Sort descending by value (Best first)
        group.sort(key=lambda x: (status_val(x), score_val(x), x['created_at']), reverse=True)
        
        keeper = group[0]
        duplicates = group[1:]
        
        print(f"  Keeping: {keeper['id']} (Status: {keeper.get('status')}, Score: {keeper.get('score_full')})")
        
        # Delete others
        for d in duplicates:
            print(f"  Deleting: {d['id']} (Status: {d.get('status')})")
            requests.delete(f"{url}/rest/v1/matches?id=eq.{d['id']}", headers=headers)
            deleted_count += 1

print(f"✅ Deduplication complete. Removed {deleted_count} duplicates.")
