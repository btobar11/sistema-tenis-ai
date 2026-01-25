import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def check_schema():
    # Try to insert a dummy match to see specific error or get structure from OPTIONS?
    # Or just get one match
    url = f"{SUPABASE_URL}/rest/v1/matches?select=*&limit=1"
    r = requests.get(url, headers=HEADERS)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if data:
            print("Columns:", data[0].keys())
        else:
            print("Table empty, cannot infer schema explicitly but access is OK.")

if __name__ == "__main__":
    check_schema()
