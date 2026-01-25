
-- Tabla de API Keys para clientes B2B (Enterprise)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL, -- Link a tabla organizations si existiera, o string per se
    key_hash TEXT NOT NULL, -- Storing hash, never raw key
    prefix TEXT NOT NULL, -- "sk_live_..." (first 8 chars) for identification
    
    plan_tier TEXT DEFAULT 'b2b_standard', -- 'b2b_standard', 'b2b_gold'
    scopes TEXT[] DEFAULT ARRAY['read:matches'], -- ['read:matches', 'read:odds']
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    expires_at TIMESTAMP WITH TIME ZONE -- Optional expiration
);

CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(prefix) WHERE is_active = TRUE;
