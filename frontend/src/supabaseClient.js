import { createClient } from '@supabase/supabase-js';

// These should be replaced with your actual Supabase URL and Anon Key
// You can find these in your Supabase project settings -> API
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
