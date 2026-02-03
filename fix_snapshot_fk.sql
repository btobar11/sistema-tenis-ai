
-- Add FK constraint to enable JOINs in PostgREST
ALTER TABLE prediction_snapshots
    ADD CONSTRAINT fk_upcoming_match
    FOREIGN KEY (upcoming_match_id)
    REFERENCES upcoming_matches(id)
    ON DELETE CASCADE;

-- Ensure RLS is still valid (re-apply public read just in case)
DROP POLICY IF EXISTS "Enable read access for all users" ON prediction_snapshots;
CREATE POLICY "Enable read access for all users" ON prediction_snapshots
    FOR SELECT USING (true);
