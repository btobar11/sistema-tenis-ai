
-- Enable RLS
ALTER TABLE upcoming_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

-- Policy for upcoming_matches (Public Read)
DROP POLICY IF EXISTS "Public Read Access" ON upcoming_matches;
CREATE POLICY "Public Read Access" ON upcoming_matches
    FOR SELECT
    USING (true);

-- Policy for upcoming_matches (Service Role Write)
DROP POLICY IF EXISTS "Service Role Write" ON upcoming_matches;
CREATE POLICY "Service Role Write" ON upcoming_matches
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy for prediction_snapshots (Public/Auth Read)
DROP POLICY IF EXISTS "Public Read Access Predictions" ON prediction_snapshots;
CREATE POLICY "Public Read Access Predictions" ON prediction_snapshots
    FOR SELECT
    USING (true);

-- Policy for prediction_snapshots (Service Role Write)
DROP POLICY IF EXISTS "Service Role Write Predictions" ON prediction_snapshots;
CREATE POLICY "Service Role Write Predictions" ON prediction_snapshots
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
