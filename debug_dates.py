
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    # Fallback to hardcoded if env vars missing in this context (often happens in dev)
    url = "https://hexpbbbsqkgowbrrorjt.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhleHBiYmJzcWtnb3dicnJvcmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzUzOTMsImV4cCI6MjA4NDUxMTM5M30.IZOYAX0jk-8VJ0C-eGBI718xKK1qFkmkGqg_MEfpuuo"

print(f"Connecting to {url}...")
supabase = create_client(url, key)

print("\n--- DB DIAGNOSTIC ---")

# 1. Check Total Count
res = supabase.table("upcoming_matches").select("*", count="exact").execute()
print(f"Total Matches in DB: {res.count}")

# 2. Check Date Distribution (First 5 and Last 5)
print("\n--- Sample Matches (Ordered by Date) ---")
res = supabase.table("upcoming_matches").select("tournament, match_date, player1_name, player2_name").order("match_date").limit(10).execute()
for m in res.data:
    print(f"[{m['match_date']}] {m['tournament']}: {m['player1_name']} vs {m['player2_name']}")

print("\n--- Matches for 'Montpellier' ---")
res = supabase.table("upcoming_matches").select("id, tournament, match_date").ilike("tournament", "%Montpellier%").execute()
if res.data:
    for m in res.data:
        print(f"[{m['match_date']}] {m['tournament']}")
else:
    print("No matches found for Montpellier.")

# 3. Check internal dates vs Today
from datetime import datetime
print(f"\nServer Time (Python): {datetime.utcnow().isoformat()}")
