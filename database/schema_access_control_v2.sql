-- LAYER 1: Profiles Schema Update
-- 1. Add 'plan' column (Missing in current schema)
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free';

-- 2. Add constraint for 'plan' integrity
ALTER TABLE profiles 
DROP CONSTRAINT IF EXISTS valid_plan_check;

ALTER TABLE profiles 
ADD CONSTRAINT valid_plan_check CHECK (plan IN ('free', 'pro', 'institutional'));

-- Note: subscription_status is already an ENUM 'subscription_tier'.
-- We assume it has values like 'free', 'basic', 'premium' based on previous context, 
-- but we will work with whatever it has.
-- If we need to add values to the enum, we can, but for now we'll stick to the existing type.

-- LAYER 2: RLS Policies (The "Wall")
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Free Users: Low Risk Only" ON prediction_snapshots;
DROP POLICY IF EXISTS "Pro Users: Full Access" ON prediction_snapshots;
DROP POLICY IF EXISTS "Institutional: Full Access" ON prediction_snapshots;

-- 1. Free Policy: High Quality Only (Trust Score >= 75)
-- Users with 'free' plan OR 'inactive' subscription
CREATE POLICY "Free Users: Low Risk Only" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (
    (SELECT plan FROM profiles WHERE id = auth.uid()) = 'free' 
    OR 
    (SELECT subscription_status::text FROM profiles WHERE id = auth.uid()) NOT IN ('active', 'premium', 'pro') -- Cast enum to text for safety
  )
  AND trust_score >= 75
);

-- 2. Pro Policy: Full Access (Active)
CREATE POLICY "Pro Users: Full Access" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (SELECT plan FROM profiles WHERE id = auth.uid()) = 'pro'
  AND (SELECT subscription_status::text FROM profiles WHERE id = auth.uid()) IN ('active', 'premium', 'trial')
);

-- 3. Institutional Policy: Full Access (Active)
CREATE POLICY "Institutional: Full Access" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (SELECT plan FROM profiles WHERE id = auth.uid()) = 'institutional'
  AND (SELECT subscription_status::text FROM profiles WHERE id = auth.uid()) = 'active'
);

-- Service Role Bypass
CREATE POLICY "Service Role Bypass" ON prediction_snapshots
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
