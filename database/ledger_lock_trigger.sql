-- Ledger Lock Trigger
-- Prevents modification of settled predictions (immutability guarantee)

CREATE OR REPLACE FUNCTION prevent_ledger_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- Only allow updates to 'pending' records
    IF OLD.result_status != 'pending' THEN
        RAISE EXCEPTION 'Cannot modify settled prediction record (immutable ledger)';
    END IF;
    
    -- Prevent deletion entirely
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Cannot delete prediction ledger records (immutable ledger)';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to prediction_ledger table
DROP TRIGGER IF EXISTS ledger_immutability ON prediction_ledger;

CREATE TRIGGER ledger_immutability
    BEFORE UPDATE OR DELETE ON prediction_ledger
    FOR EACH ROW
    EXECUTE FUNCTION prevent_ledger_modification();

-- Add index for faster resolution queries
CREATE INDEX IF NOT EXISTS idx_ledger_pending ON prediction_ledger(result_status) WHERE result_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_ledger_match ON prediction_ledger(match_id);

-- Comment for audit trail
COMMENT ON TRIGGER ledger_immutability ON prediction_ledger IS 'Prevents modification of settled predictions for audit integrity';
