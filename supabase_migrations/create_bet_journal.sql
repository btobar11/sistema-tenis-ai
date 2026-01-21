-- Create bet_journal table for tracking user bets
CREATE TABLE IF NOT EXISTS bet_journal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) NOT NULL,
    match_id UUID REFERENCES matches(id),
    player_bet_on TEXT NOT NULL,
    opponent TEXT NOT NULL,
    tournament TEXT,
    surface TEXT,
    odds DECIMAL(5,2),
    stake DECIMAL(10,2),
    result TEXT CHECK (result IN ('pending', 'won', 'lost', 'void')) DEFAULT 'pending',
    profit_loss DECIMAL(10,2),
    notes TEXT,
    bet_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bet_journal_user ON bet_journal(user_id);
CREATE INDEX IF NOT EXISTS idx_bet_journal_result ON bet_journal(result);
CREATE INDEX IF NOT EXISTS idx_bet_journal_date ON bet_journal(bet_date DESC);

-- Enable RLS
ALTER TABLE bet_journal ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only see their own bets
CREATE POLICY "Users can view own bets"
    ON bet_journal FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own bets"
    ON bet_journal FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own bets"
    ON bet_journal FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own bets"
    ON bet_journal FOR DELETE
    USING (auth.uid() = user_id);
