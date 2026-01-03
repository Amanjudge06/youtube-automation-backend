-- Create the videos table
create table public.videos (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  user_id uuid references auth.users not null,
  title text,
  description text,
  topic text,
  file_path text,
  storage_path text,
  status text,
  youtube_url text
);

-- Set up Row Level Security (RLS)
alter table public.videos enable row level security;

-- Create policies
create policy "Users can view their own videos"
  on public.videos for select
  using ( auth.uid() = user_id );

create policy "Users can insert their own videos"
  on public.videos for insert
  with check ( auth.uid() = user_id );

create policy "Users can update their own videos"
  on public.videos for update
  using ( auth.uid() = user_id );

-- Allow anonymous access for this demo app (since backend uses anon key sometimes)
-- WARNING: In production, you should use service_role key for backend operations
create policy "Enable read access for all users"
on public.videos for select
using (true);

create policy "Enable insert access for all users"
on public.videos for insert
with check (true);
