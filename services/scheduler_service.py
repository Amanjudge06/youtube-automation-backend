"""
Scheduler Service
Manages automated video creation schedules for users
Supports multiple schedules per user with different times and settings
"""

import logging
from datetime import datetime, time
from typing import List, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import pytz
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing automated video creation schedules"""
    
    def __init__(self):
        """Initialize the scheduler service"""
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=pytz.UTC
        )
        
        # Store schedule metadata
        self.schedules = {}  # {schedule_id: schedule_config}
        self.storage_file = Path("user_data/schedules.json")
        
        # Load saved schedules
        self._load_schedules()
        
        # Start the scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler service started")
    
    def _load_schedules(self):
        """Load schedules from storage"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    self.schedules = json.load(f)
                logger.info(f"📂 Loaded {len(self.schedules)} saved schedules")
                
                # Restore active schedules
                for schedule_id, schedule in self.schedules.items():
                    if schedule.get('active', False):
                        self._add_job_to_scheduler(schedule_id, schedule)
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
            self.schedules = {}
    
    def _save_schedules(self):
        """Save schedules to storage"""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.schedules, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def create_schedule(
        self,
        user_id: str,
        schedule_time: str,  # Format: "HH:MM" (24-hour)
        timezone: str = "UTC",
        config: Dict = None
    ) -> Dict:
        """
        Create a new schedule for automated video creation
        
        Args:
            user_id: User ID
            schedule_time: Time in "HH:MM" format (24-hour)
            timezone: Timezone string (e.g., "America/New_York", "Europe/London")
            config: Automation configuration (language, upload_to_youtube, etc.)
        
        Returns:
            Schedule object with ID and details
        """
        try:
            # Parse time
            hour, minute = map(int, schedule_time.split(':'))
            
            # Validate time
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError("Invalid time format. Use HH:MM (24-hour)")
            
            # Validate timezone
            try:
                tz = pytz.timezone(timezone)
            except:
                logger.warning(f"Invalid timezone {timezone}, using UTC")
                timezone = "UTC"
                tz = pytz.UTC
            
            # Generate schedule ID with microseconds to ensure uniqueness
            schedule_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            # Default config
            if config is None:
                config = {
                    'language': 'english',
                    'upload_to_youtube': True,
                    'trending_region': 'US',
                    'script_tone': 'energetic'
                }
            
            # Create schedule object
            schedule = {
                'id': schedule_id,
                'user_id': user_id,
                'schedule_time': schedule_time,
                'hour': hour,
                'minute': minute,
                'timezone': timezone,
                'config': config,
                'active': True,
                'created_at': datetime.now().isoformat(),
                'last_run': None,
                'next_run': None,
                'run_count': 0
            }
            
            # Add to scheduler
            self._add_job_to_scheduler(schedule_id, schedule)
            
            # Store schedule
            self.schedules[schedule_id] = schedule
            self._save_schedules()
            
            # Update next run time
            schedule['next_run'] = self._get_next_run_time(schedule_id)
            
            logger.info(f"✅ Created schedule {schedule_id} for {schedule_time} {timezone}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            raise
    
    def _add_job_to_scheduler(self, schedule_id: str, schedule: Dict):
        """Add a job to the APScheduler"""
        try:
            # Create cron trigger
            trigger = CronTrigger(
                hour=schedule['hour'],
                minute=schedule['minute'],
                timezone=schedule['timezone']
            )
            
            # Add job
            self.scheduler.add_job(
                func=self._run_scheduled_automation,
                trigger=trigger,
                id=schedule_id,
                args=[schedule_id],
                replace_existing=True,
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            logger.info(f"📅 Scheduled job {schedule_id} at {schedule['schedule_time']} {schedule['timezone']}")
            
        except Exception as e:
            logger.error(f"Error adding job to scheduler: {e}")
            raise
    
    def _run_scheduled_automation(self, schedule_id: str):
        """Run the automation for a scheduled job"""
        try:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                logger.error(f"Schedule {schedule_id} not found")
                return
            
            logger.info(f"🚀 Running scheduled automation: {schedule_id}")
            logger.info(f"   User: {schedule['user_id']}")
            logger.info(f"   Config: {schedule['config']}")
            
            # Import here to avoid circular imports
            from main import main
            
            # Run automation
            try:
                result = main(
                    language=schedule['config'].get('language', 'english'),
                    upload_to_youtube=schedule['config'].get('upload_to_youtube', True)
                )
                
                # Update schedule metadata
                schedule['last_run'] = datetime.now().isoformat()
                schedule['run_count'] = schedule.get('run_count', 0) + 1
                schedule['last_result'] = 'success' if result else 'failed'
                
                logger.info(f"✅ Scheduled automation completed: {schedule_id}")
                
            except Exception as e:
                logger.error(f"❌ Scheduled automation failed: {e}")
                schedule['last_result'] = f'error: {str(e)}'
            
            # Save updated schedule
            self._save_schedules()
            
        except Exception as e:
            logger.error(f"Error running scheduled automation: {e}")
    
    def get_user_schedules(self, user_id: str) -> List[Dict]:
        """Get all schedules for a user"""
        user_schedules = [
            {**schedule, 'next_run': self._get_next_run_time(schedule['id'])}
            for schedule in self.schedules.values()
            if schedule['user_id'] == user_id
        ]
        return sorted(user_schedules, key=lambda x: (x['hour'], x['minute']))
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict]:
        """Get a specific schedule"""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            schedule['next_run'] = self._get_next_run_time(schedule_id)
        return schedule
    
    def update_schedule(
        self,
        schedule_id: str,
        schedule_time: str = None,
        timezone: str = None,
        config: Dict = None,
        active: bool = None
    ) -> Dict:
        """Update an existing schedule"""
        try:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            # Update fields
            if schedule_time:
                hour, minute = map(int, schedule_time.split(':'))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    raise ValueError("Invalid time format")
                schedule['schedule_time'] = schedule_time
                schedule['hour'] = hour
                schedule['minute'] = minute
            
            if timezone:
                try:
                    pytz.timezone(timezone)
                    schedule['timezone'] = timezone
                except:
                    raise ValueError(f"Invalid timezone: {timezone}")
            
            if config:
                schedule['config'].update(config)
            
            if active is not None:
                schedule['active'] = active
            
            # Remove old job
            try:
                self.scheduler.remove_job(schedule_id)
            except:
                pass
            
            # Add updated job if active
            if schedule['active']:
                self._add_job_to_scheduler(schedule_id, schedule)
            
            # Save
            self._save_schedules()
            
            # Update next run
            schedule['next_run'] = self._get_next_run_time(schedule_id)
            
            logger.info(f"✅ Updated schedule {schedule_id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            raise
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        try:
            if schedule_id not in self.schedules:
                return False
            
            # Remove from scheduler
            try:
                self.scheduler.remove_job(schedule_id)
            except:
                pass
            
            # Remove from storage
            del self.schedules[schedule_id]
            self._save_schedules()
            
            logger.info(f"🗑️ Deleted schedule {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False
    
    def toggle_schedule(self, schedule_id: str, active: bool = None) -> Dict:
        """
        Enable or disable a schedule
        If active is None, it will toggle the current state
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # If active not specified, toggle current state
        if active is None:
            active = not schedule.get('active', True)
        
        return self.update_schedule(schedule_id, active=active)
    
    def _get_next_run_time(self, schedule_id: str) -> Optional[str]:
        """Get the next run time for a schedule"""
        try:
            job = self.scheduler.get_job(schedule_id)
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
            return None
        except:
            return None
    
    def get_all_schedules(self) -> List[Dict]:
        """Get all schedules (admin function)"""
        all_schedules = []
        for schedule_id, schedule in self.schedules.items():
            schedule_copy = schedule.copy()
            schedule_copy['next_run'] = self._get_next_run_time(schedule_id)
            all_schedules.append(schedule_copy)
        return all_schedules
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler service stopped")


# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> SchedulerService:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
