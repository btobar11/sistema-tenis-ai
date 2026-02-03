-- Phase E Refinements
-- 1. Add 'edge' column to store the calculated value at the time of snapshot
ALTER TABLE prediction_snapshots 
ADD COLUMN IF NOT EXISTS edge NUMERIC(6,3);

-- 2. Performance & Analytics Indices
CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON prediction_snapshots(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_trust_score ON prediction_snapshots(trust_score);
CREATE INDEX IF NOT EXISTS idx_snapshots_side_taken ON prediction_snapshots(side_taken);
CREATE INDEX IF NOT EXISTS idx_snapshots_edge ON prediction_snapshots(edge);

-- 3. Comment on what 'edge' means for future reference
COMMENT ON COLUMN prediction_snapshots.edge IS 'Calculated value edge (Probability * DecimalOdds - 1) at snapshot time';
