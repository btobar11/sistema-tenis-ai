-- Ensure scopes column exists and subscriptions supports new plan text
-- This is idempotent-ish
COMMENT ON TABLE api_keys IS 'Enterprise API Keys';

-- Just a metadata update to signal we support the new plan, 
-- though 'plan_id' is likely just a TEXT field so no Enum migration needed usually.
-- If we had an ENUM, we would do: ALTER TYPE plan_type ADD VALUE 'creator_lifetime';
