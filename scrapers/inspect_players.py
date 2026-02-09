import os
import requests
from dotenv import load_dotenv
from collections import defaultdict
import difflib

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

print("--- INSPECTING DUPLICATE PLAYERS ---")

# Fetch all players
resp = requests.get(f"{url}/rest/v1/players?select=id,name&order=name.asc", headers=headers)
if resp.status_code != 200:
    print(f"Error fetching players: {resp.status_code} - {resp.text}")
    exit()

players = resp.json()
# Mock ranking/country if missing from select, to avoid script error downstream
for p in players:
    p['ranking'] = p.get('ranking', 'N/A')
    p['country'] = p.get('country', 'N/A')
print(f"Total players: {len(players)}")

# Simple check: Exact name duplicates logic is usually prevented by DB constraints if 'name' is unique.
# But often names differ slightly: "J. Sinner" vs "Jannik Sinner" vs "Sinner J."

# Strategy: Group by "Last Token" (Surname) and check similarity
surname_map = defaultdict(list)

for p in players:
    name = p.get('name', '').strip()
    if not name: continue
    
    # Heuristic: Last word is surname (usually, except some formats)
    parts = name.split()
    if not parts: continue
    
    # Normalize
    surname = parts[-1].lower()
    
    # Store
    surname_map[surname].append(p)

duplicate_groups = []

for surname, group in surname_map.items():
    if len(group) > 1:
        # Check if they are actually similar
        # e.g. "Alcaraz" -> "Carlos Alcaraz", "C. Alcaraz"
        # Pairwise comparison
        done = set()
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                p1 = group[i]
                p2 = group[j]
                
                # Similarity check
                ratio = difflib.SequenceMatcher(None, p1['name'].lower(), p2['name'].lower()).ratio()
                
                if ratio > 0.6: # loose threshold for visual inspection
                    # Avoid duplicates in list
                    pair_key = tuple(sorted((p1['id'], p2['id'])))
                    if pair_key not in done:
                        duplicate_groups.append((p1, p2, ratio))
                        done.add(pair_key)

print(f"Potential Duplicates Found: {len(duplicate_groups)}")
for p1, p2, ratio in duplicate_groups[:50]: # Show top 50
    print(f"  {p1['name']} (Rank: {p1['ranking']})  <-->  {p2['name']} (Rank: {p2['ranking']})  [{ratio:.2f}]")
