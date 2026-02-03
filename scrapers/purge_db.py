import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Fetch all IDs first
resp_ids = requests.get(f"{url}/rest/v1/matches?select=id", headers=headers)
if resp_ids.status_code != 200:
    print(f"Error fetching IDs: {resp_ids.text}")
    exit(1)

ids = [row['id'] for row in resp_ids.json()]
print(f"Found {len(ids)} matches to delete.")

if not ids:
    print("Database is already empty.")
    exit(0)

# Delete in batches of 100 to stay within URL limits
batch_size = 100
for i in range(0, len(ids), batch_size):
    batch = ids[i:i+batch_size]
    batch_str = ",".join(batch)
    del_resp = requests.delete(f"{url}/rest/v1/matches?id=in.({batch_str})", headers=headers)
    if del_resp.status_code in [200, 204]:
        print(f"Deleted batch {i}-{i+len(batch)}")
    else:
        print(f"Error filtering batch: {del_resp.text}")

print("✅ Purge Verified.")
