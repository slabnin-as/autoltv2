import logging
from datetime import datetime, timedelta
from app import db
from app.models.jira_task import JiraTask
from app.models.scheduler import Scheduler
from app.services.jira_service import JiraService
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class TaskSchedulerService:
    """Service for automatic task scheduling in EKPLT project"""
    
    def __init__(self):
        self.jira_service = JiraService()
        self.slot_duration_hours = 4
        self.start_hour = 19  # 19:00
    
    def schedule_next_tasks(self) -> dict:
        """
        Main method to schedule next available tasks
        Returns summary of scheduled tasks
        """
        logger.info("🔄 Starting task scheduling process...")
        
        # 1. Get tasks with status 'Open' ordered by planned_start
        open_tasks = self._get_open_tasks()
        if not open_tasks:
            return {"scheduled": 0, "message": "No open tasks found"}
        
        logger.info(f"📋 Found {len(open_tasks)} open tasks")
        
        # 2. Schedule each task in available slots
        scheduled_count = 0
        results = []
        
        for task in open_tasks:
            try:
                slot_time = self._find_next_available_slot()
                if slot_time:
                    success = self._schedule_task(task, slot_time)
                    if success:
                        scheduled_count += 1
                        results.append({
                            "task": task.jira_key,
                            "slot_start": slot_time,
                            "slot_end": slot_time + timedelta(hours=self.slot_duration_hours)
                        })
                        logger.info(f"✅ Scheduled {task.jira_key} for {slot_time}")
                    else:
                        logger.error(f"❌ Failed to schedule {task.jira_key}")
                else:
                    logger.warning(f"⏰ No available slot found for {task.jira_key}")
                    break  # No more slots available
            except Exception as e:
                logger.error(f"❌ Error scheduling {task.jira_key}: {e}")
        
        return {
            "scheduled": scheduled_count,
            "tasks": results,
            "message": f"Successfully scheduled {scheduled_count} tasks"
        }
    
    def _get_open_tasks(self) -> List[JiraTask]:
        """Get tasks with status 'Open' ordered by planned_start date"""
        return JiraTask.query.filter(
            JiraTask.status == 'Open'
        ).order_by(
            JiraTask.planned_start.asc()
        ).all()
    
    def _find_next_available_slot(self) -> Optional[datetime]:
        """
        Find next available 4-hour slot starting from today 19:00
        Returns None if no slot available
        """
        # Start from today at 19:00
        now = datetime.now()
        current_date = now.date()
        
        # If it's past 23:00 today, start from tomorrow
        if now.hour >= 23:
            current_date = current_date + timedelta(days=1)
        
        # Check next 30 days for available slots
        for day_offset in range(30):
            check_date = current_date + timedelta(days=day_offset)
            slot_start = datetime.combine(check_date, datetime.min.time()) + timedelta(hours=self.start_hour)
            slot_end = slot_start + timedelta(hours=self.slot_duration_hours)
            
            # Check if this slot is free (no overlapping tasks)
            if self._is_slot_available(slot_start, slot_end):
                return slot_start
        
        return None
    
    def _is_slot_available(self, slot_start: datetime, slot_end: datetime) -> bool:
        """
        Check if time slot is available (no overlapping scheduled tasks)
        """
        # Check scheduler table for overlapping tasks
        overlapping_tasks = Scheduler.query.filter(
            Scheduler.status.in_(['ready', 'running']),
            Scheduler.planned_start < slot_end,
            (Scheduler.planned_start + timedelta(hours=self.slot_duration_hours)) > slot_start
        ).count()
        
        return overlapping_tasks == 0
    
    def _schedule_task(self, task: JiraTask, slot_time: datetime) -> bool:
        """
        Schedule a task for the given slot time
        1. Update JIRA (status to 'In Progress', set planned_start and planned_end)
        2. Save to scheduler table
        """
        try:
            slot_end = slot_time + timedelta(hours=self.slot_duration_hours)
            
            # 1. Update JIRA task
            jira_updated = self._update_jira_task(task.jira_key, slot_time, slot_end)
            if not jira_updated:
                logger.warning(f"⚠️ Failed to update JIRA for task {task.jira_key}")
                return False
            
            # 2. Update local database
            task.status = 'In Progress'
            task.planned_start = slot_time
            db.session.commit()
            
            # 3. Create scheduler entry
            scheduler_entry = Scheduler(
                jira_task=task.jira_key,
                planned_start=slot_time,
                status='ready'
            )
            db.session.add(scheduler_entry)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error scheduling task {task.jira_key}: {e}")
            return False
    
    def _update_jira_task(self, jira_key: str, planned_start: datetime, planned_end: datetime) -> bool:
        """
        Update JIRA task with new status and timing
        Returns True if successful
        """
        try:
            return self.jira_service.update_task_status_and_timing(jira_key, planned_start, planned_end)
        except Exception as e:
            logger.error(f"❌ JIRA update failed for {jira_key}: {e}")
            return False
    
    def get_scheduling_status(self) -> dict:
        """Get current scheduling status and statistics"""
        total_open = JiraTask.query.filter(JiraTask.status == 'Open').count()
        total_scheduled = Scheduler.query.filter(Scheduler.status == 'ready').count()
        total_running = Scheduler.query.filter(Scheduler.status == 'running').count()
        
        return {
            "open_tasks": total_open,
            "scheduled_tasks": total_scheduled,
            "running_tasks": total_running,
            "slot_duration_hours": self.slot_duration_hours,
            "start_time": f"{self.start_hour}:00"
        }