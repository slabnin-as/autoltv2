import logging
import time
from datetime import datetime, timedelta
from app import db
from app.models.scheduler import Scheduler
from app.models.jenkins_job_config import JenkinsJobConfig
from app.services.jenkins_service import JenkinsService

logger = logging.getLogger(__name__)

class AutoLTService:
    """Service for AutoLT pipeline execution"""
    
    def __init__(self):
        self.jenkins_service = JenkinsService()
    
    def run_autolt_process(self):
        """
        Main AutoLT process - checks for ready tasks scheduled for current hour
        """
        logger.info("🤖 Starting AutoLT process...")

        # Get current time rounded to the hour
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        next_hour = current_hour + timedelta(hours=1)

        logger.info(f"🕐 Looking for tasks scheduled for {current_hour.strftime('%Y-%m-%d %H:%M')}")

        # Find tasks with status 'ready' and planned_start matching current hour
        ready_tasks = Scheduler.query.filter(
            Scheduler.status == 'ready',
            Scheduler.planned_start >= current_hour,
            Scheduler.planned_start < next_hour
        ).all()

        if not ready_tasks:
            logger.info("ℹ️ No ready tasks found for current hour")
            return {"message": "No ready tasks found for current hour", "processed": 0}
        
        logger.info(f"📋 Found {len(ready_tasks)} ready tasks")
        processed_count = 0
        
        for task in ready_tasks:
            try:
                logger.info(f"🔄 Processing task {task.jira_task} with pipeline {task.pipeline}")
                
                if task.pipeline == 'EKP':
                    self._execute_ekp_pipeline(task)
                elif task.pipeline == 'INFOSRV':
                    self._execute_infosrv_pipeline(task)
                else:
                    logger.warning(f"⚠️ Unknown pipeline: {task.pipeline} for task {task.jira_task}")
                    continue
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing task {task.jira_task}: {e}")
                # Set task status to FAIL
                task.status = 'FAIL'
                db.session.commit()
        
        logger.info(f"✅ AutoLT process completed. Processed {processed_count} tasks")
        return {"message": f"Processed {processed_count} tasks", "processed": processed_count}
    
    def _execute_ekp_pipeline(self, task: Scheduler):
        """Execute EKP pipeline"""
        logger.info(f"🎯 Starting EKP pipeline for task {task.jira_task}")
        
        # Phase 1: Check and start required jobs
        if not self._check_and_start_ekp_jobs(task):
            return
        
        # Phase 2: Wait for warmup (30 minutes)
        logger.info("⏰ Waiting 30 minutes for environment warmup...")
        time.sleep(30 * 60)  # 30 minutes
        
        # Phase 3: Test BEFORE phase
        self._execute_test_before_phase(task, 'test-project-build')
        
        # Phase 4: Deploy phase
        self._execute_deploy_phase(task)
        
        # Phase 5: Test AFTER phase
        self._execute_test_after_phase(task, 'test-project-build')
        
        # Phase 6: Generate report
        self._execute_report_phase(task)
        
        logger.info(f"✅ EKP pipeline completed for task {task.jira_task}")
    
    def _execute_infosrv_pipeline(self, task: Scheduler):
        """Execute INFOSRV pipeline"""
        logger.info(f"🎯 Starting INFOSRV pipeline for task {task.jira_task}")
        
        # Phase 1: Check and start required jobs
        if not self._check_and_start_infosrv_jobs(task):
            return
        
        # Phase 2: Wait for warmup (30 minutes)
        logger.info("⏰ Waiting 30 minutes for environment warmup...")
        time.sleep(30 * 60)  # 30 minutes
        
        # Phase 3: Test BEFORE phase
        self._execute_test_before_phase(task, 'infosrv_only')
        
        # Phase 4: Deploy phase
        self._execute_deploy_phase(task)
        
        # Phase 5: Test AFTER phase
        self._execute_test_after_phase(task, 'infosrv_only')
        
        # Phase 6: Generate report
        self._execute_report_phase(task)
        
        logger.info(f"✅ INFOSRV pipeline completed for task {task.jira_task}")
    
    def _check_and_start_ekp_jobs(self, task: Scheduler) -> bool:
        """Check and start EKP jobs: Start_EKP_pipe and test-project-build"""
        logger.info("🔍 Checking EKP pipeline jobs status...")
        
        # Check job status
        start_ekp_running = self._is_job_running('Start_EKP_pipe')
        test_build_running = self._is_job_running('test-project-build')
        
        logger.info(f"📊 Job status - Start_EKP_pipe: {'Running' if start_ekp_running else 'Stopped'}, test-project-build: {'Running' if test_build_running else 'Stopped'}")
        
        if not start_ekp_running and not test_build_running:
            # Both stopped - start Start_EKP_pipe
            logger.info("🚀 Starting Start_EKP_pipe...")
            success, message = self.jenkins_service.trigger_job('Start_EKP_pipe')
            if not success:
                logger.error(f"❌ Failed to start Start_EKP_pipe: {message}")
                task.status = 'FAIL'
                db.session.commit()
                return False
        
        elif start_ekp_running and not test_build_running:
            # Only start test-project-build
            logger.info("🚀 Starting test-project-build...")
            success, message = self.jenkins_service.trigger_job('test-project-build')
            if not success:
                logger.error(f"❌ Failed to start test-project-build: {message}")
                task.status = 'FAIL'
                db.session.commit()
                return False
        
        elif not start_ekp_running and test_build_running:
            # Start_EKP_pipe stopped but test-project-build running - FAIL
            logger.error("❌ Invalid state: Start_EKP_pipe stopped but test-project-build running")
            task.status = 'FAIL'
            db.session.commit()
            return False
        
        # Both running - continue
        return True
    
    def _check_and_start_infosrv_jobs(self, task: Scheduler) -> bool:
        """Check and start INFOSRV jobs: Start_infosrv_pipe and infosrv_only"""
        logger.info("🔍 Checking INFOSRV pipeline jobs status...")
        
        # Check job status
        start_infosrv_running = self._is_job_running('Start_infosrv_pipe')
        infosrv_only_running = self._is_job_running('infosrv_only')
        
        logger.info(f"📊 Job status - Start_infosrv_pipe: {'Running' if start_infosrv_running else 'Stopped'}, infosrv_only: {'Running' if infosrv_only_running else 'Stopped'}")
        
        if not start_infosrv_running and not infosrv_only_running:
            # Both stopped - start Start_infosrv_pipe
            logger.info("🚀 Starting Start_infosrv_pipe...")
            success, message = self.jenkins_service.trigger_job('Start_infosrv_pipe')
            if not success:
                logger.error(f"❌ Failed to start Start_infosrv_pipe: {message}")
                task.status = 'FAIL'
                db.session.commit()
                return False
        
        elif start_infosrv_running and not infosrv_only_running:
            # Only start infosrv_only
            logger.info("🚀 Starting infosrv_only...")
            success, message = self.jenkins_service.trigger_job('infosrv_only')
            if not success:
                logger.error(f"❌ Failed to start infosrv_only: {message}")
                task.status = 'FAIL'
                db.session.commit()
                return False
        
        elif not start_infosrv_running and infosrv_only_running:
            # Start_infosrv_pipe stopped but infosrv_only running - FAIL
            logger.error("❌ Invalid state: Start_infosrv_pipe stopped but infosrv_only running")
            task.status = 'FAIL'
            db.session.commit()
            return False
        
        # Both running - continue
        return True
    
    def _execute_test_before_phase(self, task: Scheduler, test_job_name: str):
        """Execute test BEFORE phase"""
        logger.info(f"🧪 Starting test BEFORE phase for task {task.jira_task}")
        
        # Update status and start time
        task.status = 'test_before'
        task.stage_before_start = datetime.utcnow()
        db.session.commit()
        
        # Wait 60 minutes for test
        logger.info("⏰ Running tests for 60 minutes...")
        time.sleep(60 * 60)  # 60 minutes
        
        # Fix end time and stop test job
        task.stage_before_end = datetime.utcnow()
        db.session.commit()
        
        # Stop test job
        logger.info(f"🛑 Stopping {test_job_name}...")
        self._stop_job(test_job_name)
        
        logger.info("✅ Test BEFORE phase completed")
    
    def _execute_deploy_phase(self, task: Scheduler):
        """Execute deploy phase"""
        logger.info(f"🚀 Starting deploy phase for task {task.jira_task}")
        
        # Update status and start time
        task.status = 'deploy'
        task.stage_deploy_start = datetime.utcnow()
        db.session.commit()
        
        # Trigger deploy job and wait for completion
        logger.info("🚀 Starting job.deploy...")
        success, message = self.jenkins_service.trigger_job('job.deploy')
        
        if not success:
            logger.error(f"❌ Failed to start job.deploy: {message}")
            task.status = 'FAIL'
            db.session.commit()
            return
        
        # Wait for job completion (implement job monitoring)
        self._wait_for_job_completion('job.deploy')
        
        # Fix end time
        task.stage_deploy_end = datetime.utcnow()
        db.session.commit()
        
        logger.info("✅ Deploy phase completed")
    
    def _execute_test_after_phase(self, task: Scheduler, test_job_name: str):
        """Execute test AFTER phase"""
        logger.info(f"🧪 Starting test AFTER phase for task {task.jira_task}")
        
        # Start test job again
        logger.info(f"🚀 Starting {test_job_name}...")
        self.jenkins_service.trigger_job(test_job_name)
        
        # Wait for warmup again (30 minutes)
        logger.info("⏰ Waiting 30 minutes for environment warmup...")
        time.sleep(30 * 60)  # 30 minutes
        
        # Update status and start time
        task.status = 'test_after'
        task.stage_after_start = datetime.utcnow()
        db.session.commit()
        
        # Wait 60 minutes for test
        logger.info("⏰ Running tests for 60 minutes...")
        time.sleep(60 * 60)  # 60 minutes
        
        # Fix end time and stop test job
        task.stage_after_end = datetime.utcnow()
        db.session.commit()
        
        # Stop test job
        logger.info(f"🛑 Stopping {test_job_name}...")
        self._stop_job(test_job_name)
        
        logger.info("✅ Test AFTER phase completed")
    
    def _execute_report_phase(self, task: Scheduler):
        """Execute report generation phase"""
        logger.info(f"📊 Starting report generation for task {task.jira_task}")
        
        # Update status
        task.status = 'generating_report'
        db.session.commit()
        
        # Trigger report job
        logger.info("🚀 Starting create_report...")
        success, message = self.jenkins_service.trigger_job('create_report')
        
        if success:
            task.status = 'completed'
            logger.info("✅ Report generation started, task completed")
        else:
            task.status = 'FAIL'
            logger.error(f"❌ Failed to start create_report: {message}")
        
        db.session.commit()
    
    def _is_job_running(self, job_name: str) -> bool:
        """Check if Jenkins job is currently running"""
        try:
            # Use Jenkins service to check job status
            job_info = self.jenkins_service.get_job_info(job_name)
            if job_info:
                # Check if there are any running builds
                return job_info.get('color', '') == 'blue_anime' or job_info.get('inQueue', False)
            return False
        except Exception as e:
            logger.warning(f"⚠️ Could not check status for job {job_name}: {e}")
            return False
    
    def _stop_job(self, job_name: str):
        """Stop Jenkins job"""
        try:
            success, message = self.jenkins_service.stop_job(job_name)
            if success:
                logger.info(f"✅ Job {job_name} stopped successfully")
            else:
                logger.warning(f"⚠️ Could not stop job {job_name}: {message}")
        except Exception as e:
            logger.warning(f"⚠️ Could not stop job {job_name}: {e}")
    
    def _wait_for_job_completion(self, job_name: str, timeout_minutes: int = 60):
        """Wait for job completion with timeout"""
        logger.info(f"⏰ Waiting for {job_name} to complete...")
        start_time = datetime.utcnow()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.utcnow() - start_time < timeout:
            if not self._is_job_running(job_name):
                logger.info(f"✅ Job {job_name} completed")
                return True
            
            time.sleep(30)  # Check every 30 seconds
        
        logger.warning(f"⚠️ Job {job_name} did not complete within {timeout_minutes} minutes")
        return False