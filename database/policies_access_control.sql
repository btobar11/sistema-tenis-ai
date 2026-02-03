-- Enable RLS on prediction_snapshots
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

-- create a helper function to check subscription status
CREATE OR REPLACE FUNCTION public.get_subscription_status()
RETURNS text AS $$
DECLARE
  sub_status text;
BEGIN
  SELECT subscription_status INTO sub_status
  FROM profiles
  WHERE id = auth.uid();
  
  RETURN COALESCE(sub_status, 'free');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- POLICY: Free Users (Trust Score <= 70% OR Older than 24h)
-- Free users see "High Confidence" picks only if they are old (history), 
-- OR they see "Lower Confidence" picks live (teaser).
-- Actually user asked: "Free: Acceso parcial... Trust Score <= X"
CREATE POLICY "Free Users: Low Confidence Only" ON prediction_snapshots
FOR SELECT
TO authenticated
USING (
  (get_subscription_status() = 'free' AND trust_score <= 70)
  OR
  (get_subscription_status() IN ('premium', 'pro', 'institutional'))
);

-- POLICY: Service Role (Full Access)
CREATE POLICY "Service Role: Full Access" ON prediction_snapshots
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
