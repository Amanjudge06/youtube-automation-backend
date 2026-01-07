-- Schedules table for persistent storage of automation schedules
-- This ensures schedules survive Cloud Run container restarts

CREATE TABLE IF NOT EXISTS schedules (
    schedule_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    schedule_time TEXT NOT NULL,  -- Format: "HH:MM"
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    config JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_run TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    last_result TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster user queries
CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);

-- Index for active schedules
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(active);

-- Enable Row Level Security
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;

-- Drop old restrictive policies if they exist
DROP POLICY IF EXISTS "Users can view their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can insert their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can update their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can delete their own schedules" ON schedules;
DROP POLICY IF EXISTS "Allow demo_user full access" ON schedules;

-- Create permissive policies for all authenticated users
CREATE POLICY "Allow authenticated users full access"
    ON schedules FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Also allow public/anon access (for users not logged in via Supabase auth)
CREATE POLICY "Allow public access"
    ON schedules FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);
