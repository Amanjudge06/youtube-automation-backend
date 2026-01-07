"""
Test script to verify scheduler automation execution
This will create a schedule that runs in 2 minutes and wait for it
"""
import time
import logging
from datetime import datetime, timedelta
import pytz
from services.scheduler_service import get_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_scheduler():
    """Test that the scheduler actually runs the automation at scheduled time"""
    
    # Initialize scheduler
    logger.info("🚀 Initializing scheduler...")
    scheduler = get_scheduler()
    
    # Calculate time 2 minutes from now
    now = datetime.now(pytz.UTC)
    test_time = now + timedelta(minutes=2)
    time_str = test_time.strftime("%H:%M")
    
    logger.info(f"⏰ Current time: {now.strftime('%H:%M:%S')} UTC")
    logger.info(f"📅 Creating schedule for: {time_str} UTC (in ~2 minutes)")
    
    # Create test schedule with YouTube upload disabled
    schedule = scheduler.create_schedule(
        user_id='test_user',
        schedule_time=time_str,
        timezone='UTC',
        config={
            'language': 'english',
            'upload_to_youtube': False,  # Don't upload to YouTube in test
            'trending_region': 'US',
            'script_tone': 'energetic'
        }
    )
    
    logger.info(f"✅ Schedule created: {schedule['id']}")
    logger.info(f"   Next run: {schedule['next_run']}")
    
    # Check schedule status
    logger.info(f"\n📊 Scheduler Status:")
    logger.info(f"   Active schedules: {len(scheduler.schedules)}")
    logger.info(f"   Active jobs: {len(scheduler.scheduler.get_jobs())}")
    
    for job in scheduler.scheduler.get_jobs():
        logger.info(f"   • Job: {job.id}")
        logger.info(f"     Next run: {job.next_run_time}")
    
    # Wait and monitor
    logger.info(f"\n⏳ Waiting for scheduled execution...")
    logger.info(f"   This test will wait for 3 minutes")
    logger.info(f"   Watch for: '🚀 Running scheduled automation' message\n")
    
    # Monitor for 3 minutes
    start_time = time.time()
    initial_run_count = schedule.get('run_count', 0)
    
    while time.time() - start_time < 180:  # 3 minutes
        time.sleep(10)  # Check every 10 seconds
        
        # Refresh schedule data
        schedule = scheduler.get_schedule(schedule['id'])
        if schedule and schedule.get('run_count', 0) > initial_run_count:
            logger.info(f"\n✅ SUCCESS! Schedule executed at scheduled time")
            logger.info(f"   Run count: {schedule['run_count']}")
            logger.info(f"   Last run: {schedule.get('last_run')}")
            logger.info(f"   Result: {schedule.get('last_result')}")
            return True
        
        # Log status every 30 seconds
        if int(time.time() - start_time) % 30 == 0:
            remaining = 180 - int(time.time() - start_time)
            logger.info(f"   Still waiting... ({remaining}s remaining)")
    
    logger.error(f"\n❌ Schedule did not execute in expected time")
    return False

if __name__ == "__main__":
    try:
        success = test_scheduler()
        if success:
            logger.info(f"\n🎉 Scheduler test PASSED - automation runs at scheduled times!")
        else:
            logger.warning(f"\n⚠️  Scheduler test FAILED - check logs above")
    except KeyboardInterrupt:
        logger.info(f"\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
