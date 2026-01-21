import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='scrapers/.env')

url_base = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url_base or not key:
    print("Missing credentials")
    exit(1)

api_url = f"{url_base}/rest/v1/players"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates" # Upsert behavior
}

def upload_batch(batch):
    # Mapping keys if necessary. data.json has: name, rank_single, country, plays_hand, points
    # DB has: name, rank_single, plays_hand, country (and others ignored)
    # PostgREST fails if unknown columns are sent.
    
    clean_batch = []
    for p in batch:
        clean_batch.append({
            "name": p["name"],
            "rank_single": p["rank_single"],
            "plays_hand": p.get("plays_hand", "U"),
            "country": p.get("country", "UNK")
        })
    
    try:
        r = requests.post(api_url, headers=headers, json=clean_batch)
        if r.status_code in [200, 201]:
            print(f"Batch success: {len(batch)} rows.")
        else:
            print(f"Batch failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    with open('scrapers/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total records to upload: {len(data)}")
    
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        print(f"Uploading batch {i} to {i+len(batch)}...")
        upload_batch(batch)

if __name__ == "__main__":
    main()
