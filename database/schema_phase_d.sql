-- Phase D: Validation & Trust Metrics Schema Update
-- Add columns to predictions table

ALTER TABLE predictions ADD COLUMN IF NOT EXISTS confidence NUMERIC(4,3);
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS engine_reason TEXT;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS dq_score NUMERIC(4,3); -- Data Quality
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS ss_score NUMERIC(4,3); -- Simulation Stability (Variance)

-- Optional: Add index on confidence for querying high-trust picks
CREATE INDEX IF NOT EXISTS idx_predictions_confidence ON predictions(confidence);
