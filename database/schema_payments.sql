
-- Tabla de Suscripciones (Fuente de Verdad de Acceso B2C)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- References auth.users(id) - but we use text/uuid depending on auth setup
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan_id TEXT NOT NULL DEFAULT 'free', -- free, pro_monthly, elite_monthly
    status TEXT NOT NULL DEFAULT 'active', -- active, past_due, canceled, incomplete
    
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast access checks
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
