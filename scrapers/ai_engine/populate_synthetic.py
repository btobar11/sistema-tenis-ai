import os
import requests
import random
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_path, '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def populate_synthetic_data(num_matches=1000):
    print(f"Generating {num_matches} synthetic matches...")
    
    # 1. Create/Get Dummy Players
    top_players = [
        "Jannik Sinner", "Carlos Alcaraz", "Novak Djokovic", "Daniil Medvedev", 
        "Alexander Zverev", "Andrey Rublev", "Holger Rune", "Casper Ruud",
        "Stefanos Tsitsipas", "Hubert Hurkacz", "Taylor Fritz", "Grigor Dimitrov",
        "Tommy Paul", "Ben Shelton", "Frances Tiafoe", "Karen Khachanov"
    ]
    
    player_ids = []
    print("Upserting players...")
    for name in top_players:
        payload = {"name": name, "plays_hand": "R", "country": "UNK"}
        try:
            r = requests.post(f"{SUPABASE_URL}/rest/v1/players", 
                             headers={**HEADERS, "Prefer": "return=representation,resolution=merge-duplicates"}, 
                             json=payload)
            if r.status_code in [200, 201] and r.json():
                player_ids.append(r.json()[0]['id'])
            else:
                if r.status_code == 409:
                    # Fetch existing
                    url_get = f"{SUPABASE_URL}/rest/v1/players?name=eq.{name}&select=id"
                    r2 = requests.get(url_get, headers=HEADERS)
                    if r2.status_code == 200 and r2.json():
                        player_ids.append(r2.json()[0]['id'])
                        print(f"    Found existing {name}")
                else:
                     print(f"    Failed {name}: {r.status_code} - {r.text[:100]}")
        except Exception as e:
            print(f"Error player {name}: {e}")
            
    if len(player_ids) < 2:
        print("Not enough players.")
        return

    # 2. Generate Matches
    matches = []
    surfaces = ['hard', 'clay', 'grass']
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_matches):
        p1 = random.choice(player_ids)
        p2 = random.choice(player_ids)
        if p1 == p2: continue
        
        date = start_date + timedelta(days=random.randint(0, 365))
        surface = random.choice(surfaces)
        
        # Determine winner (random for synthetic, but keep some consistency if we wanted)
        winner = p1 if random.random() > 0.5 else p2
        
        # Score
        score = "6-4 6-4" if random.random() > 0.5 else "6-3 4-6 6-4"
        
        match = {
            "tournament_name": f"Synthetic Open {surface}",
            "date": date.strftime("%Y-%m-%d"),
            "surface": surface,
            "player1_id": p1, # In DB schema, p1/p2 fields, winner_id indicates outcome
            "player2_id": p2,
            "winner_id": winner,
            "score_full": score,
            "stats_json": {"generated": True}
        }
        matches.append(match)
        
        if len(matches) >= 100:
            # Batch Insert
            # print(f"Debug Match Payload: {matches[0]}")
            r = requests.post(f"{SUPABASE_URL}/rest/v1/matches", headers=HEADERS, json=matches)
            if r.status_code != 201:
                print(f"Error inserting batch: {r.text}") # Full text
            else:
                print(f"Inserted batch of {len(matches)}")
            matches = []

    print("Synthetic population complete.")

if __name__ == "__main__":
    populate_synthetic_data(1000)
