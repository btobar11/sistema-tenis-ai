import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(dotenv_path='scrapers/.env')

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
# Mask key for log
print(f"Key: {key[:5]}...")

try:
    supabase: Client = create_client(url, key)
    response = supabase.table("players").select("count", count="exact").execute()
    print(f"Connection successful! Count: {response.count}")
except Exception as e:
    print(f"Connection failed: {e}")
