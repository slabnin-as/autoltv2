from datetime import datetime
import jenkins
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from config.config import Config

class JenkinsService:
    def __init__(self):
        self.connections = {}  # Cache for multiple Jenkins connections
        self.default_server = None
        self._connect_default()
    
    def _connect_default(self):
        """Connect to default Jenkins server from config"""
        try:
            self.default_server = jenkins.Jenkins(
                Config.JENKINS_URL,
                username=Config.JENKINS_USERNAME,
                password=Config.JENKINS_TOKEN
            )
            self.default_server.get_whoami()
        except Exception as e:
            print(f"Failed to connect to Jenkins: {e}")
            self.default_server = None
    
    def _get_jenkins_connection(self, jenkins_url, username=None, token=None):
        """Get or create Jenkins connection for specific instance"""
        # Use provided credentials or fall back to default
        auth_username = username or Config.JENKINS_USERNAME
        auth_token = token or Config.JENKINS_TOKEN
        
        # Create connection key for caching
        connection_key = f"{jenkins_url}:{auth_username}"
        
        if connection_key not in self.connections:
            try:
                self.connections[connection_key] = jenkins.Jenkins(
                    jenkins_url,
                    username=auth_username,
                    password=auth_token
                )
                # Test connection
                self.connections[connection_key].get_whoami()
            except Exception as e:
                print(f"Failed to connect to Jenkins {jenkins_url}: {e}")
                self.connections[connection_key] = None
        
        return self.connections[connection_key]
    
    def trigger_job_by_config(self, job_config_id, parameters=None):
        """Trigger a Jenkins job using JenkinsJobConfig"""
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return False, f"Job configuration {job_config_id} not found"
        
        # Get connection for this specific Jenkins instance
        jenkins_conn = self._get_jenkins_connection(job_config.project_url)
        
        if not jenkins_conn:
            return False, f"Cannot connect to Jenkins instance: {job_config.project_url}"
        
        try:
            if parameters:
                jenkins_conn.build_job(job_config.job_name, parameters)
            else:
                jenkins_conn.build_job(job_config.job_name)
            
            return True, f"Job {job_config.job_name} triggered successfully"
        except Exception as e:
            return False, f"Failed to trigger job: {str(e)}"
    
    def trigger_job(self, job_name, parameters=None):
        """Trigger job on default Jenkins server"""
        if not self.default_server:
            return False, "Default Jenkins connection not available"
        
        try:
            if parameters:
                build_number = self.default_server.build_job(job_name, parameters)
            else:
                build_number = self.default_server.build_job(job_name)
            
            return True, f"Job triggered successfully. Build number: {build_number}"
        except Exception as e:
            return False, f"Failed to trigger job: {e}"
    
    def get_all_configs(self, project=None):
        """Get all job configurations, optionally filtered by project"""
        query = JenkinsJobConfig.query
        if project:
            query = query.filter_by(project=project)
        
        return query.order_by(JenkinsJobConfig.job_name).all()
    
    def get_all_projects(self):
        """Get list of all projects with their job counts"""
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
        """Get current status of a job"""
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return {"error": "Job configuration not found"}
        
        # Get connection for this specific Jenkins instance
        jenkins_conn = self._get_jenkins_connection(job_config.project_url)
        
        if not jenkins_conn:
            return {"error": "Jenkins server not connected"}
        
        try:
            job_info = jenkins_conn.get_job_info(job_config.job_name)
            return job_info
        except Exception as e:
            return {"error": "Could not retrieve job status"}
    
    def get_job_info(self, job_name, jenkins_url=None):
        """Get job info from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            jenkins_conn = self.default_server
            
        if not jenkins_conn:
            return None
        
        try:
            return jenkins_conn.get_job_info(job_name)
        except Exception as e:
            print(f"Error getting job info for {job_name}: {e}")
            return None
    
    def get_build_info(self, job_name, build_number, jenkins_url=None):
        """Get build info from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            jenkins_conn = self.default_server
            
        if not jenkins_conn:
            return None
        
        try:
            return jenkins_conn.get_build_info(job_name, build_number)
        except Exception as e:
            print(f"Error getting build info for {job_name}#{build_number}: {e}")
            return None
    
    def list_jobs(self, jenkins_url=None):
        """List jobs from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            jenkins_conn = self.default_server
            
        if not jenkins_conn:
            return []
        
        try:
            return jenkins_conn.get_jobs()
        except Exception as e:
            print(f"Error listing Jenkins jobs: {e}")
            return []