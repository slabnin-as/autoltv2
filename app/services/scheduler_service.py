from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.jenkins_service import JenkinsService
from app.models.jenkins_job_config import JenkinsJobConfig
from app import db

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jenkins_service = JenkinsService()
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        self.scheduler.start()
    
    def add_scheduled_job(self, job_id, cron_expression, jenkins_job_name, parameters=None):
        try:
            # Parse cron expression and create trigger
            cron_parts = cron_expression.split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                trigger = CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )
            else:
                raise ValueError("Invalid cron expression format")
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_jenkins_job,
                trigger=trigger,
                id=job_id,
                args=[jenkins_job_name, parameters],
                replace_existing=True
            )
            
            # Update next execution time in database
            job_record = JenkinsJobConfig.query.filter_by(name=jenkins_job_name).first()
            if job_record:
                next_run = self.scheduler.get_job(job_id).next_run_time
                job_record.next_execution = next_run
                db.session.commit()
            
            return True, "Job scheduled successfully"
        except Exception as e:
            return False, f"Failed to schedule job: {e}"
    
    def remove_scheduled_job(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            return True, "Job removed from schedule"
        except Exception as e:
            return False, f"Failed to remove job: {e}"
    
    def _execute_jenkins_job(self, jenkins_job_name, parameters=None):
        try:
            success, message = self.jenkins_service.trigger_job(jenkins_job_name, parameters)
            
            # Update job record
            job_record = JenkinsJobConfig.query.filter_by(name=jenkins_job_name).first()
            if job_record:
                job_record.last_execution = datetime.utcnow()
                if success:
                    job_record.last_build_status = "TRIGGERED"
                db.session.commit()
            
            print(f"Scheduled job execution: {jenkins_job_name} - {message}")
        except Exception as e:
            print(f"Error executing scheduled job {jenkins_job_name}: {e}")
    
    def get_scheduled_jobs(self):
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def update_job_schedules(self):
        active_jobs = JenkinsJobConfig.query.filter_by(is_active=True).all()
        for job in active_jobs:
            if job.schedule:
                job_id = f"jenkins_{job.id}"
                self.add_scheduled_job(
                    job_id=job_id,
                    cron_expression=job.schedule,
                    jenkins_job_name=job.name,
                    parameters=job.parameters
                )
    
    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()