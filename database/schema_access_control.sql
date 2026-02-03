-- LAYER 1: Single Source of Truth (Profiles)
-- Update profiles table with subscription details
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive',
ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP WITH TIME ZONE;

-- Add constraints for data integrity
ALTER TABLE profiles 
DROP CONSTRAINT IF EXISTS valid_plan_check;
ALTER TABLE profiles 
ADD CONSTRAINT valid_plan_check CHECK (plan IN ('free', 'pro', 'institutional'));

ALTER TABLE profiles
DROP CONSTRAINT IF EXISTS valid_status_check;
ALTER TABLE profiles
ADD CONSTRAINT valid_status_check CHECK (subscription_status IN ('active', 'trial', 'inactive', 'canceled'));

-- LAYER 2: RLS Policies (The "Wall")
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Free Users: Low Risk Only" ON prediction_snapshots;
DROP POLICY IF EXISTS "Pro Users: Full Access" ON prediction_snapshots;
DROP POLICY IF EXISTS "Institutional: Full Access" ON prediction_snapshots;
DROP POLICY IF EXISTS "Free Users: Low Confidence Only" ON prediction_snapshots; -- previous attempt

-- 1. Free Policy: High Quality Only (Trust Score >= 75)
-- "Enseñas calidad, no cantidad"
CREATE POLICY "Free Users: Low Risk Only" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (SELECT plan FROM profiles WHERE id = auth.uid()) = 'free' 
  AND trust_score >= 75
);

-- 2. Pro Policy: Full Access (Active/Trial)
CREATE POLICY "Pro Users: Full Access" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (SELECT plan FROM profiles WHERE id = auth.uid()) = 'pro'
  AND (SELECT subscription_status FROM profiles WHERE id = auth.uid()) IN ('active', 'trial')
);

-- 3. Institutional Policy: Full Access (Active)
CREATE POLICY "Institutional: Full Access" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (SELECT plan FROM profiles WHERE id = auth.uid()) = 'institutional'
  AND (SELECT subscription_status FROM profiles WHERE id = auth.uid()) = 'active'
);

-- Service Role Bypass (for Admin/Testing)
CREATE POLICY "Service Role Bypass" ON prediction_snapshots
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
