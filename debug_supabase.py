import logging
import config
from services.supabase_service import SupabaseService
import uuid
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dummy_file(filename, size_mb):
    with open(filename, "wb") as f:
        f.seek(size_mb * 1024 * 1024 - 1)
        f.write(b"\0")

def test_supabase():
    print("Testing Supabase Connection...")
    service = SupabaseService()
    
    if not service.is_available():
        print("❌ Supabase service not available (check config)")
        return

    print("✅ Supabase service initialized")
    
    # 1. Test Large File Upload (55MB) - Expect Failure
    print("\nTesting 55MB File Upload (Expect Failure)...")
    try:
        filename = "test_large.bin"
        create_dummy_file(filename, 55)
        
        from pathlib import Path
        path = Path(filename)
        storage_path = f"debug/{uuid.uuid4()}_large.bin"
        
        url = service.upload_file("videos", storage_path, path)
        if url:
            print(f"✅ Upload successful (Unexpected): {url}")
        else:
            print("❌ Upload failed (Expected if limit is 50MB)")
            
        os.remove(filename)
        
    except Exception as e:
        print(f"❌ Storage error (Expected): {e}")
        if os.path.exists(filename):
            os.remove(filename)

    # 2. Test Small File Upload (20MB) - Expect Success
    print("\nTesting 20MB File Upload (Expect Success)...")
    try:
        filename = "test_small.bin"
        create_dummy_file(filename, 20)
        
        from pathlib import Path
        path = Path(filename)
        storage_path = f"debug/{uuid.uuid4()}_small.bin"
        
        url = service.upload_file("videos", storage_path, path)
        if url:
            print(f"✅ Upload successful: {url}")
        else:
            print("❌ Upload failed (Unexpected)")
            
        os.remove(filename)
        
    except Exception as e:
        print(f"❌ Storage error: {e}")
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_supabase()
