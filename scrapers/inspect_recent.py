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

print("--- Inspecting Latest Matches (Requests) ---")
resp = requests.get(f"{url}/rest/v1/matches?select=*,player1:player1_id(name),player2:player2_id(name)&order=date.desc&limit=5", headers=headers)

if resp.status_code != 200:
    print(f"Error: {resp.text}")
else:
    matches = resp.json()
    for m in matches:
        p1 = m.get('player1', {}).get('name', 'Unknown')
        p2 = m.get('player2', {}).get('name', 'Unknown')
        t_name = m.get('tournament_name') or m.get('tournament') or 'Unknown Tourn'
        print(f"[{m.get('date')}] {p1} vs {p2} ({t_name})")
        print(f"   Winner Name: {m.get('winner_name')} | Winner ID: {m.get('winner_id')}")
        print(f"   Status: {m.get('status')} | Score: {m.get('score_full')}")

