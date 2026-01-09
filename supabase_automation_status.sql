-- Create automation_status table in Supabase
-- Run this in Supabase SQL Editor

-- Create table
CREATE TABLE IF NOT EXISTS automation_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'demo_user',
    running BOOLEAN DEFAULT false,
    current_step TEXT DEFAULT '',
    progress INTEGER DEFAULT 0,
    logs JSONB DEFAULT '[]'::jsonb,
    error TEXT,
    video_path TEXT,
    youtube_url TEXT,
    last_run TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_automation_status_user_id ON automation_status(user_id);

-- Enable RLS
ALTER TABLE automation_status ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for demo
DROP POLICY IF EXISTS "Allow all access to automation_status" ON automation_status;
CREATE POLICY "Allow all access to automation_status"
    ON automation_status FOR ALL
    USING (true)
    WITH CHECK (true);

-- Insert default row for demo_user
INSERT INTO automation_status (user_id, running, current_step, progress, logs)
VALUES ('demo_user', false, '', 0, '[]'::jsonb)
ON CONFLICT DO NOTHING;

-- Verify
SELECT * FROM automation_status;
