-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Create profiles table
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  email text,
  full_name text,
  avatar_url text,
  updated_at timestamp with time zone
);

-- Create videos table
create table if not exists public.videos (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references auth.users on delete cascade not null,
  title text not null,
  description text,
  topic text,
  file_path text,
  storage_path text,
  thumbnail_url text,
  duration float,
  status text default 'completed',
  youtube_url text,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;
alter table public.videos enable row level security;

-- Create policies for profiles
create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- Create policies for videos
create policy "Users can view their own videos."
  on videos for select
  using ( auth.uid() = user_id );

create policy "Users can insert their own videos."
  on videos for insert
  with check ( auth.uid() = user_id );

create policy "Users can update their own videos."
  on videos for update
  using ( auth.uid() = user_id );

create policy "Users can delete their own videos."
  on videos for delete
  using ( auth.uid() = user_id );

-- Create storage bucket for videos if it doesn't exist
insert into storage.buckets (id, name, public)
values ('videos', 'videos', true)
on conflict (id) do nothing;

-- Storage policies
create policy "Video Access"
  on storage.objects for select
  using ( bucket_id = 'videos' );

create policy "Video Upload"
  on storage.objects for insert
  with check ( bucket_id = 'videos' and auth.uid() = owner );

create policy "Video Update"
  on storage.objects for update
  with check ( bucket_id = 'videos' and auth.uid() = owner );

create policy "Video Delete"
  on storage.objects for delete
  using ( bucket_id = 'videos' and auth.uid() = owner );

-- Function to handle new user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

-- Trigger for new user signup
create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
