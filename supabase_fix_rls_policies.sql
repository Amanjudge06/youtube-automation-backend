-- Migration script to fix RLS policies for schedules table
-- Run this in Supabase SQL Editor to fix the permission issues

-- Drop old restrictive policies
DROP POLICY IF EXISTS "Users can view their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can insert their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can update their own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can delete their own schedules" ON schedules;
DROP POLICY IF EXISTS "Allow demo_user full access" ON schedules;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON schedules;
DROP POLICY IF EXISTS "Allow public access" ON schedules;

-- Create new permissive policies
CREATE POLICY "Allow authenticated users full access"
    ON schedules FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow public access"
    ON schedules FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- Verify policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'schedules';
