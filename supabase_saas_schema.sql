-- Complete SaaS Schema for YouTube Automation Platform
-- Run this in Supabase SQL Editor after enabling Authentication

-- ========================================
-- 1. USER SETTINGS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- API Keys (encrypted in application layer)
    google_api_key TEXT,
    pexels_api_key TEXT,
    pixabay_api_key TEXT,
    elevenlabs_api_key TEXT,
    
    -- YouTube OAuth tokens (stored securely)
    youtube_credentials JSONB,
    
    -- User preferences
    default_voice_id TEXT DEFAULT 'EXAVITQu4vr4xnSDxMaL',
    default_trending_region TEXT DEFAULT 'US',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ========================================
-- 2. SCHEDULES TABLE (with user isolation)
-- ========================================
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    schedule_time TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add missing columns if table already exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='schedules' AND column_name='is_active') THEN
        ALTER TABLE schedules ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='schedules' AND column_name='created_at') THEN
        ALTER TABLE schedules ADD COLUMN created_at TIMESTAMPTZ DEFAULT now();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='schedules' AND column_name='updated_at') THEN
        ALTER TABLE schedules ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active, user_id);

-- ========================================
-- 3. AUTOMATION STATUS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS automation_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Status tracking
    running BOOLEAN DEFAULT false,
    current_step TEXT DEFAULT '',
    progress INTEGER DEFAULT 0,
    logs JSONB DEFAULT '[]'::jsonb,
    error TEXT,
    
    -- Output info
    video_path TEXT,
    youtube_url TEXT,
    youtube_video_id TEXT,
    
    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_run TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_automation_status_user_id ON automation_status(user_id);
CREATE INDEX IF NOT EXISTS idx_automation_status_running ON automation_status(running, user_id);

-- ========================================
-- 4. VIDEO HISTORY TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS video_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Video details
    topic TEXT NOT NULL,
    title TEXT,
    description TEXT,
    tags TEXT[],
    
    -- Files
    video_path TEXT,
    thumbnail_path TEXT,
    script_path TEXT,
    
    -- YouTube info
    youtube_video_id TEXT,
    youtube_url TEXT,
    upload_status TEXT DEFAULT 'pending',
    
    -- Analytics
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    
    -- Generation metadata
    generation_time_seconds INTEGER,
    error TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    uploaded_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_video_history_user_id ON video_history(user_id);
CREATE INDEX IF NOT EXISTS idx_video_history_created_at ON video_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_history_youtube_id ON video_history(youtube_video_id);

-- ========================================
-- 5. USER USAGE TRACKING
-- ========================================
CREATE TABLE IF NOT EXISTS user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Usage limits
    videos_generated_today INTEGER DEFAULT 0,
    videos_generated_month INTEGER DEFAULT 0,
    total_videos_generated INTEGER DEFAULT 0,
    
    -- Plan limits
    plan_type TEXT DEFAULT 'free', -- free, basic, pro, enterprise
    max_videos_per_day INTEGER DEFAULT 3,
    max_videos_per_month INTEGER DEFAULT 30,
    
    -- Last reset timestamps
    daily_reset_at TIMESTAMPTZ DEFAULT date_trunc('day', now()),
    monthly_reset_at TIMESTAMPTZ DEFAULT date_trunc('month', now()),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);

-- ========================================
-- 6. USER PROFILES (extended user info)
-- ========================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Profile info
    full_name TEXT,
    avatar_url TEXT,
    
    -- Subscription
    subscription_status TEXT DEFAULT 'active', -- active, canceled, expired
    subscription_tier TEXT DEFAULT 'free',
    subscription_started_at TIMESTAMPTZ,
    subscription_expires_at TIMESTAMPTZ,
    
    -- Onboarding
    onboarding_completed BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- ========================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ========================================

-- Enable RLS on all tables
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- USER SETTINGS POLICIES
DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;
CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own settings" ON user_settings;
CREATE POLICY "Users can delete own settings" ON user_settings
    FOR DELETE USING (auth.uid() = user_id);

-- SCHEDULES POLICIES
DROP POLICY IF EXISTS "Users can view own schedules" ON schedules;
CREATE POLICY "Users can view own schedules" ON schedules
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own schedules" ON schedules;
CREATE POLICY "Users can insert own schedules" ON schedules
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own schedules" ON schedules;
CREATE POLICY "Users can update own schedules" ON schedules
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own schedules" ON schedules;
CREATE POLICY "Users can delete own schedules" ON schedules
    FOR DELETE USING (auth.uid() = user_id);

-- AUTOMATION STATUS POLICIES
DROP POLICY IF EXISTS "Users can view own status" ON automation_status;
CREATE POLICY "Users can view own status" ON automation_status
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own status" ON automation_status;
CREATE POLICY "Users can insert own status" ON automation_status
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own status" ON automation_status;
CREATE POLICY "Users can update own status" ON automation_status
    FOR UPDATE USING (auth.uid() = user_id);

-- VIDEO HISTORY POLICIES
DROP POLICY IF EXISTS "Users can view own videos" ON video_history;
CREATE POLICY "Users can view own videos" ON video_history
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own videos" ON video_history;
CREATE POLICY "Users can insert own videos" ON video_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own videos" ON video_history;
CREATE POLICY "Users can update own videos" ON video_history
    FOR UPDATE USING (auth.uid() = user_id);

-- USER USAGE POLICIES
DROP POLICY IF EXISTS "Users can view own usage" ON user_usage;
CREATE POLICY "Users can view own usage" ON user_usage
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own usage" ON user_usage;
CREATE POLICY "Users can update own usage" ON user_usage
    FOR UPDATE USING (auth.uid() = user_id);

-- USER PROFILES POLICIES
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- ========================================
-- 8. TRIGGERS FOR UPDATED_AT
-- ========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_schedules_updated_at ON schedules;
CREATE TRIGGER update_schedules_updated_at
    BEFORE UPDATE ON schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_automation_status_updated_at ON automation_status;
CREATE TRIGGER update_automation_status_updated_at
    BEFORE UPDATE ON automation_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_video_history_updated_at ON video_history;
CREATE TRIGGER update_video_history_updated_at
    BEFORE UPDATE ON video_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_usage_updated_at ON user_usage;
CREATE TRIGGER update_user_usage_updated_at
    BEFORE UPDATE ON user_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 9. AUTOMATIC USER INITIALIZATION
-- ========================================
-- Create a function to initialize user data on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create user profile
    INSERT INTO public.user_profiles (user_id)
    VALUES (NEW.id);
    
    -- Create user settings
    INSERT INTO public.user_settings (user_id)
    VALUES (NEW.id);
    
    -- Create user usage tracking
    INSERT INTO public.user_usage (user_id)
    VALUES (NEW.id);
    
    -- Create automation status
    INSERT INTO public.automation_status (user_id, running, progress)
    VALUES (NEW.id, false, 0);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create user data on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ========================================
-- 10. HELPER FUNCTIONS
-- ========================================

-- Function to check if user has reached daily limit
CREATE OR REPLACE FUNCTION check_daily_limit(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
    v_limit INTEGER;
BEGIN
    SELECT videos_generated_today, max_videos_per_day
    INTO v_count, v_limit
    FROM user_usage
    WHERE user_id = p_user_id;
    
    RETURN v_count < v_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to increment usage counter
CREATE OR REPLACE FUNCTION increment_usage(p_user_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE user_usage
    SET 
        videos_generated_today = videos_generated_today + 1,
        videos_generated_month = videos_generated_month + 1,
        total_videos_generated = total_videos_generated + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to reset daily usage (call via cron job)
CREATE OR REPLACE FUNCTION reset_daily_usage()
RETURNS void AS $$
BEGIN
    UPDATE user_usage
    SET 
        videos_generated_today = 0,
        daily_reset_at = date_trunc('day', now())
    WHERE daily_reset_at < date_trunc('day', now());
END;
$$ LANGUAGE plpgsql;

-- Function to reset monthly usage (call via cron job)
CREATE OR REPLACE FUNCTION reset_monthly_usage()
RETURNS void AS $$
BEGIN
    UPDATE user_usage
    SET 
        videos_generated_month = 0,
        monthly_reset_at = date_trunc('month', now())
    WHERE monthly_reset_at < date_trunc('month', now());
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- VERIFICATION
-- ========================================
-- Check that all tables were created successfully
SELECT 
    schemaname, tablename, tableowner 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'user_settings', 
        'schedules', 
        'automation_status', 
        'video_history', 
        'user_usage', 
        'user_profiles'
    )
ORDER BY tablename;

-- Verify RLS is enabled
SELECT 
    schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'user_settings', 
        'schedules', 
        'automation_status', 
        'video_history', 
        'user_usage', 
        'user_profiles'
    )
ORDER BY tablename;
