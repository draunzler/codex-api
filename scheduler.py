from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import List
import asyncio
import logging

from database import UserProfile, Cache
from genshin_client import genshin_client
from config import settings


class DataUpdateScheduler:
    """Scheduler for automatic user data updates."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the scheduler."""
        if not self.is_running:
            # Schedule user data updates every 4 hours
            self.scheduler.add_job(
                self.update_all_users,
                IntervalTrigger(hours=settings.update_interval),
                id='update_users',
                name='Update all user data',
                replace_existing=True
            )
            
            # Schedule cache cleanup every hour
            self.scheduler.add_job(
                self.cleanup_cache,
                IntervalTrigger(hours=1),
                id='cleanup_cache',
                name='Cleanup expired cache',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            self.logger.info("Data update scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("Data update scheduler stopped")
    
    async def update_all_users(self):
        """Update data for all users with auto-update enabled."""
        try:
            self.logger.info("Starting scheduled user data update")
            
            # Get all users that need updates
            users = await UserProfile.get_all_for_update()
            
            if not users:
                self.logger.info("No users found for update")
                return
            
            self.logger.info(f"Updating data for {len(users)} users")
            
            # Update users in batches to avoid overwhelming the API
            batch_size = 5
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [self.update_user_data(user["uid"]) for user in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait between batches to respect rate limits
                if i + batch_size < len(users):
                    await asyncio.sleep(10)
            
            self.logger.info("Scheduled user data update completed")
            
        except Exception as e:
            self.logger.error(f"Error in scheduled update: {str(e)}")
    
    async def update_user_data(self, uid: int):
        """Update data for a specific user."""
        try:
            self.logger.info(f"Updating data for user {uid}")
            
            # Fetch fresh data from Genshin API
            user_data = await genshin_client.fetch_user_data(uid)
            
            # Update user profile in database
            await UserProfile.update(uid, user_data)
            
            self.logger.info(f"Successfully updated data for user {uid}")
            
        except Exception as e:
            self.logger.error(f"Error updating user {uid}: {str(e)}")
    
    async def cleanup_cache(self):
        """Clean up expired cache entries."""
        try:
            deleted_count = await Cache.cleanup_expired()
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired cache entries")
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {str(e)}")
    
    async def force_update_user(self, uid: int):
        """Force update for a specific user (manual trigger)."""
        try:
            await self.update_user_data(uid)
            return {"success": True, "message": f"User {uid} data updated successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_next_update_time(self) -> datetime:
        """Get the next scheduled update time."""
        job = self.scheduler.get_job('update_users')
        if job:
            return job.next_run_time
        return None
    
    def get_scheduler_status(self) -> dict:
        """Get scheduler status information."""
        return {
            "running": self.is_running,
            "next_update": self.get_next_update_time(),
            "update_interval_hours": settings.update_interval,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time
                }
                for job in self.scheduler.get_jobs()
            ]
        }


# Singleton instance
scheduler = DataUpdateScheduler() 