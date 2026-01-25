-- Add metadata columns to players table
ALTER TABLE players 
ADD COLUMN IF NOT EXISTS birth_date DATE,
ADD COLUMN IF NOT EXISTS height TEXT,
ADD COLUMN IF NOT EXISTS weight TEXT,
ADD COLUMN IF NOT EXISTS photo_url TEXT,
ADD COLUMN IF NOT EXISTS current_rank INTEGER;

-- Create index for name search if not exists
CREATE INDEX IF NOT EXISTS idx_players_name_trgm ON players USING gin (name gin_trgm_ops);
