from datetime import datetime
import jenkins
from app import db
from app.models.jenkins_job import JenkinsJob
from config.config import Config

class JenkinsService:
    def __init__(self):
        self.server = None
        self._connect()
    
    def _connect(self):
        try:
            self.server = jenkins.Jenkins(
                Config.JENKINS_URL,
                username=Config.JENKINS_USERNAME,
                password=Config.JENKINS_TOKEN
            )
            # Test connection
            self.server.get_whoami()
        except Exception as e:
            print(f"Failed to connect to Jenkins: {e}")
            self.server = None
    
    def trigger_job(self, job_name, parameters=None):
        if not self.server:
            return False, "Jenkins connection not available"
        
        try:
            if parameters:
                build_number = self.server.build_job(job_name, parameters)
            else:
                build_number = self.server.build_job(job_name)
            
            # Update job record in database
            job_record = JenkinsJob.query.filter_by(name=job_name).first()
            if job_record:
                job_record.last_execution = datetime.utcnow()
                db.session.commit()
            
            return True, f"Job triggered successfully. Build number: {build_number}"
        except Exception as e:
            return False, f"Failed to trigger job: {e}"
    
    def get_job_info(self, job_name):
        if not self.server:
            return None
        
        try:
            return self.server.get_job_info(job_name)
        except Exception as e:
            print(f"Error getting job info for {job_name}: {e}")
            return None
    
    def get_build_info(self, job_name, build_number):
        if not self.server:
            return None
        
        try:
            return self.server.get_build_info(job_name, build_number)
        except Exception as e:
            print(f"Error getting build info for {job_name}#{build_number}: {e}")
            return None
    
    def update_job_status(self, job_name):
        if not self.server:
            return
        
        try:
            job_info = self.server.get_job_info(job_name)
            if not job_info:
                return
            
            job_record = JenkinsJob.query.filter_by(name=job_name).first()
            if job_record:
                last_build = job_info.get('lastBuild')
                if last_build:
                    build_info = self.server.get_build_info(job_name, last_build['number'])
                    job_record.last_build_number = last_build['number']
                    job_record.last_build_status = build_info.get('result', 'UNKNOWN')
                
                db.session.commit()
        except Exception as e:
            print(f"Error updating job status for {job_name}: {e}")
    
    def list_jobs(self):
        if not self.server:
            return []
        
        try:
            return self.server.get_jobs()
        except Exception as e:
            print(f"Error listing Jenkins jobs: {e}")
            return []