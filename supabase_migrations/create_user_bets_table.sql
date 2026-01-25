-- Create 'user_bets' table
CREATE TABLE IF NOT EXISTS user_bets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  match_id UUID REFERENCES matches(id),
  selection_id UUID, -- ID of the player chosen (fk to players, optional constrain)
  amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
  odds DECIMAL(5, 2) NOT NULL DEFAULT 1.00,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'won', 'lost', 'void')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  profit DECIMAL(10, 2) DEFAULT 0
);

-- RLS Policies
ALTER TABLE user_bets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own bets"
ON user_bets FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own bets"
ON user_bets FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bets"
ON user_bets FOR UPDATE
USING (auth.uid() = user_id);
