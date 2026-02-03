import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print("--- Searching for Montpellier Matches ---")
# Search for matches with specific player names or tournament
# We'll fetch all today/recent and filter in python for fuzzy matching or use ilike if possible.
# Supabase REST 'ilike' is handy.

# Try finding 'Vavassori'
print("Checking Player: Vavassori...")
# We need to find the player ID first usually, or join.
# Let's just dump the last 20 matches and look at names.
resp = requests.get(f"{url}/rest/v1/matches?select=*,player1:player1_id(name),player2:player2_id(name)&order=created_at.desc&limit=20", headers=headers)

if resp.status_code == 200:
    matches = resp.json()
    found = False
    for m in matches:
        p1 = m.get('player1', {}).get('name', 'Unknown')
        p2 = m.get('player2', {}).get('name', 'Unknown')
        status = m.get('status')
        score = m.get('score_full')
        winner = m.get('winner_name')
        
        # Check if relevant
        if 'Vavassori' in p1 or 'Vavassori' in p2 or 'Fils' in p1 or 'Fils' in p2 or 'Humbert' in p1:
            found = True
            print(f"✅ FOUND REAL MATCH: {p1} vs {p2}")
            print(f"   Status: {status} | Winner: {winner} | Score: {score}")
            print(f"   Tournament: {m.get('tournament_name')}")
            print("-" * 30)
            
    if not found:
        print("⚠️ No specific Montpellier matches found in the last 20 insertions yet.")
        print("Last match inserted:", matches[0]['player1']['name'], "vs", matches[0]['player2']['name'] if matches else "None")
else:
    print("Error fetching matches.")
