import os
import sys
import logging
from supabase import create_client

# Add current directory to path so we can import config
sys.path.append(os.getcwd())
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_tables():
    url = config.SUPABASE_URL
    key = config.SUPABASE_KEY
    
    if not url or not key:
        logger.error("❌ SUPABASE_URL or SUPABASE_KEY not found in config")
        return

    try:
        supabase = create_client(url, key)
        logger.info(f"Connecting to Supabase at {url}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        return

    tables_to_check = [
        'user_settings',
        'schedules',
        'automation_status',
        'video_history',
        'user_usage',
        'user_profiles'
    ]

    all_good = True

    for table in tables_to_check:
        try:
            # Try to select 1 row to see if table exists
            response = supabase.table(table).select("*", count='exact').limit(0).execute()
            logger.info(f"✅ Table '{table}' exists")

            # Check for user_id column in critical tables
            if table in ['schedules', 'automation_status']:
                try:
                    supabase.table(table).select('user_id').limit(0).execute()
                    logger.info(f"   ✅ Column 'user_id' exists in '{table}'")
                except Exception:
                    logger.warning(f"   ⚠️  Column 'user_id' MISSING in '{table}' - Migration needed!")

            
        except Exception as e:
            # The python client might raise an exception if the table doesn't exist
            # or return an error in the response structure depending on version
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                 logger.error(f"❌ Table '{table}' DOES NOT EXIST")
            else:
                 logger.error(f"❌ Error accessing '{table}': {error_msg}")
            all_good = False

    if all_good:
        print("\n✅ All SaaS tables appear to execute successfully. Schema seems valid.")
    else:
        print("\n⚠️  Some tables are missing. Please run the SQL migration Script in Supabase SQL Editor.")

if __name__ == "__main__":
    verify_tables()
