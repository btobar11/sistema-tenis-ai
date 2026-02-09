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

print("--- Inspecting Vavassori Matches ---")
# Fetch matches involving Vavassori
# We need to find his ID or just filter by name if possible?
# Let's fetch recent matches and filter in python again for clarity.
resp = requests.get(f"{url}/rest/v1/matches?select=*,player1:player1_id(name),player2:player2_id(name)&order=created_at.desc&limit=100", headers=headers)

if resp.status_code == 200:
    matches = resp.json()
    for m in matches:
        p1 = m.get('player1', {}).get('name', 'Unknown')
        p2 = m.get('player2', {}).get('name', 'Unknown')
        
        if 'Vavassori' in p1 or 'Vavassori' in p2:
            print(f"ID: {m['id']}")
            print(f"   Date: {m['date']}")
            print(f"   Match: {p1} vs {p2}")
            print(f"   Status: {m.get('status')} | Round: {m.get('round')}")
            print(f"   Source/Created: {m.get('created_at')}")
            print("-" * 20)
else:
    print("Error fetching")
