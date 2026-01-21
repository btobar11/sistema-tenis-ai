import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

def check_schema():
    url = f"{SUPABASE_URL}/rest/v1/matches?select=*&limit=1"
    r = requests.get(url, headers=HEADERS)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if data:
            print("Keys found:", list(data[0].keys()))
        else:
            print("Table matches is empty.")
    else:
        print(r.text)

if __name__ == "__main__":
    check_schema()
