
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
