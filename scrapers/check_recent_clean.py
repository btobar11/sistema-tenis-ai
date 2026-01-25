import requests
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def clean_more_junk():
    print("Checking for more junk players (single digits)...")
    # Check for names like '3', '4', '5', '6', '0'
    url = f"{SUPABASE_URL}/rest/v1/players?name=in.(0,3,4,5,6,7,8,9)&select=id,name"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        players = r.json()
        print(f"Found {len(players)} matched junk players: {players}")
        for p in players:
             pid = p['id']
             print(f"Deleting matches for {p['name']}...")
             requests.delete(f"{SUPABASE_URL}/rest/v1/matches?player1_id=eq.{pid}", headers=headers)
             requests.delete(f"{SUPABASE_URL}/rest/v1/matches?player2_id=eq.{pid}", headers=headers)
             requests.delete(f"{SUPABASE_URL}/rest/v1/players?id=eq.{pid}", headers=headers)
             print(f"Deleted {p['name']}")
    else:
        print(f"Error: {r.text}")

if __name__ == "__main__":
    clean_more_junk()
