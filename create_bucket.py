import os
from supabase import create_client
import config

def create_bucket():
    url = config.SUPABASE_URL
    key = config.SUPABASE_KEY
    
    if not url or not key:
        print("Supabase credentials missing")
        return

    supabase = create_client(url, key)
    
    try:
        # Try to create the 'videos' bucket
        # Note: This might fail if the key doesn't have permissions
        # But for public buckets it might work if RLS allows it
        print("Attempting to create 'videos' bucket...")
        res = supabase.storage.create_bucket('videos', options={'public': True})
        print(f"Bucket created: {res}")
    except Exception as e:
        print(f"Error creating bucket: {e}")
        
        # List buckets to see if it exists
        try:
            buckets = supabase.storage.list_buckets()
            print(f"Existing buckets: {buckets}")
        except Exception as e2:
            print(f"Error listing buckets: {e2}")

if __name__ == "__main__":
    create_bucket()
