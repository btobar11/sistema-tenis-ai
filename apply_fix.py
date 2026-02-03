
import os
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL") or "https://hexpbbbsqkgowbrrorjt.supabase.co"
key = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhleHBiYmJzcWtnb3dicnJvcmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzUzOTMsImV4cCI6MjA4NDUxMTM5M30.IZOYAX0jk-8VJ0C-eGBI718xKK1qFkmkGqg_MEfpuuo"

supabase: Client = create_client(url, key)

print("Attempting to apply Foreign Key constraint...")

sql = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_upcoming_match') THEN
        ALTER TABLE prediction_snapshots
        ADD CONSTRAINT fk_upcoming_match
        FOREIGN KEY (upcoming_match_id)
        REFERENCES upcoming_matches(id)
        ON DELETE CASCADE;
    END IF;
END $$;
"""

# Try to check if we can execute this (PostgREST doesn't support generic SQL exec easily without RPC)
# But since we have the Supabase CLI installed, let's use subprocess to be robust.

import subprocess

try:
    with open("temp_fix.sql", "w") as f:
        f.write(sql)
    
    # Use the npx command with redirection handled by python
    # This avoids PowerShell encoding issues
    cmd = ["npx", "supabase", "db", "execute", "--project-ref", "hexpbbbsqkgowbrrorjt"]
    
    with open("temp_fix.sql", "r") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, shell=True)
        
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("SUCCESS: Constraint applied.")
    else:
        print("FAILURE: Could not apply constraint.")

except Exception as e:
    print(f"Error: {e}")
