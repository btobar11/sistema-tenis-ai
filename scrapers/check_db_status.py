import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in env")
    exit(1)

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "count=exact"
}

print("--- Database Diagnostics (REST) ---")

# 1. Matches Count
try:
    # Use select=id to minimize data transfer, count=exact in header
    resp = requests.get(f"{url}/rest/v1/matches?select=id&limit=1", headers=headers)
    if resp.status_code in [200, 206]:
        content_range = resp.headers.get("Content-Range") # Format: 0-0/123
        if content_range:
            total = content_range.split('/')[-1]
            print(f"Matches Count: {total}")
        else:
            print(f"Matches Count: Unknown (No Content-Range Header). Body len: {len(resp.json())}")
    else:
        print(f"Error checking matches: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Exception checking matches: {e}")

# 2. User Bets Existence
try:
    resp = requests.get(f"{url}/rest/v1/user_bets?select=*&limit=1", headers=headers)
    if resp.status_code == 200:
        print("Table 'user_bets': EXISTS")
    elif resp.status_code == 404:
         print("Table 'user_bets': NOT FOUND (404)")
    else:
        print(f"Table 'user_bets': Error {resp.status_code} - {resp.text}")

except Exception as e:
    print(f"Exception checking user_bets: {e}")

print("-----------------------------------")
