
import subprocess
import os

sql_content = """
-- Fix Foreign Key
ALTER TABLE prediction_snapshots
DROP CONSTRAINT IF EXISTS fk_upcoming_match;

ALTER TABLE prediction_snapshots
ADD CONSTRAINT fk_upcoming_match
FOREIGN KEY (upcoming_match_id)
REFERENCES upcoming_matches(id)
ON DELETE CASCADE;

-- Ensure RLS
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Read Snapshots" ON prediction_snapshots;
CREATE POLICY "Public Read Snapshots" ON prediction_snapshots FOR SELECT USING (true);
"""

print("Writing SQL file...")
with open("final_fix.sql", "w") as f:
    f.write(sql_content)

print("Executing via npx supabase...")
# Use shell=True for windows piping consistency, but simplistic approach
cmd = "npx supabase db execute --project-ref hexpbbbsqkgowbrrorjt < final_fix.sql"

try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("SUCCESS: Fix applied.")
    else:
        print("FAILURE: npx returned non-zero.")
except Exception as e:
    print("Error:", e)
