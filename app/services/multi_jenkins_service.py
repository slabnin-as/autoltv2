import jenkins
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from config.config import Config

class MultiJenkinsService:
    """
    Simple Jenkins service for managing job configurations
    """
    
    def __init__(self):
        self.server = None
        self._connect()
    
    def _connect(self):
        """Connect to Jenkins server"""
        try:
            self.server = jenkins.Jenkins(
                Config.JENKINS_URL,
                username=Config.JENKINS_USERNAME,
                password=Config.JENKINS_TOKEN
            )
            self.server.get_whoami()
        except Exception as e:
            print(f"Failed to connect to Jenkins: {e}")
            self.server = None
    
    def trigger_job_by_config(self, job_config_id, parameters=None):
        """
        Trigger a Jenkins job using JenkinsJobConfig
        """
        if not self.server:
            return False, "Jenkins server not connected"
            
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return False, f"Job configuration {job_config_id} not found"
        
        try:
            # Use project_url as the complete job path
            if parameters:
                self.server.build_job(job_config.job_name, parameters)
            else:
                self.server.build_job(job_config.job_name)
            
            return True, f"Job {job_config.job_name} triggered successfully"
        except Exception as e:
            return False, f"Failed to trigger job: {str(e)}"
    
    def get_all_configs(self, project=None):
        """
        Get all job configurations, optionally filtered by project
        """
        query = JenkinsJobConfig.query
        if project:
            query = query.filter_by(project=project)
        
        return query.order_by(JenkinsJobConfig.job_name).all()
    
    def get_all_projects(self):
        """
        Get list of all projects with their job counts
        """
        projects = db.session.query(
            JenkinsJobConfig.project,
            db.func.count(JenkinsJobConfig.id).label('job_count')
        ).group_by(JenkinsJobConfig.project).all()
        
        return [
            {
                'project_name': project.project,
                'total_jobs': project.job_count
            }
            for project in projects
        ]
    
    def get_job_status(self, job_config_id):
        """
        Get current status of a job
        """
        if not self.server:
            return {"error": "Jenkins server not connected"}
            
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return {"error": "Job configuration not found"}
        
        try:
            job_info = self.server.get_job_info(job_config.job_name)
            return job_info
        except Exception as e:
            return {"error": "Could not retrieve job status"}