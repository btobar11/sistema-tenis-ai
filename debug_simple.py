
import os
from supabase import create_client

url = "https://hexpbbbsqkgowbrrorjt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhleHBiYmJzcWtnb3dicnJvcmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzUzOTMsImV4cCI6MjA4NDUxMTM5M30.IZOYAX0jk-8VJ0C-eGBI718xKK1qFkmkGqg_MEfpuuo"

print("Connecting...")
try:
    supabase = create_client(url, key)
    
    # Simple count
    res = supabase.table("upcoming_matches").select("id", count="exact").execute()
    print("Total Rows:", res.count)
    
    # Get recent/future matches
    res = supabase.table("upcoming_matches").select("tournament, match_date").order("match_date", desc=True).limit(10).execute()
    
    print("--- Latest 10 Matches in DB ---")
    for m in res.data:
        print(f"Date: {m['match_date']} | Tourn: {m['tournament']}")

except Exception as e:
    print("Error:", e)
