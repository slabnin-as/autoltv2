import logging
from datetime import datetime
import jenkins
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.models.user_data import UserData
from config.config import Config

logger = logging.getLogger(__name__)

class JenkinsService:
    def __init__(self):
        self.connections = {}  # Cache for multiple Jenkins connections
        self.default_server = None
        self._default_connected = False
    
    def _ensure_default_connection(self):
        """Ensure default connection is established"""
        if not self._default_connected:
            self._connect_default()

    def _connect_default(self, jenkins_service='jenkins'):
        """Connect to default Jenkins server using database credentials first"""
        try:
            # Try to get credentials from database first
            jenkins_creds = None
            try:
                jenkins_creds = UserData.get_credentials(jenkins_service)
                if not jenkins_creds and jenkins_service != 'jenkins':
                    # Fallback to generic jenkins if specific service not found
                    jenkins_creds = UserData.get_credentials('jenkins')
            except Exception as e:
                logger.warning(f"⚠️ Could not access database for Jenkins credentials: {e}")

            if jenkins_creds:
                logger.info(f"🔑 Using Jenkins credentials from database for service: {jenkins_service}, user: {jenkins_creds.name or 'default'}")
                username = jenkins_creds.name or Config.JENKINS_USERNAME
                token = jenkins_creds.token
                jenkins_url = Config.JENKINS_URL
            else:
                logger.warning(f"⚠️ No Jenkins credentials found for service {jenkins_service}, using environment variables")
                username = Config.JENKINS_USERNAME
                token = Config.JENKINS_TOKEN
                jenkins_url = Config.JENKINS_URL
            
            self.default_server = jenkins.Jenkins(
                jenkins_url,
                username=username,
                password=token
            )
            self.default_server.get_whoami()
            self._default_connected = True

        except Exception as e:
            logger.error(f"Failed to connect to Jenkins: {e}")
            self.default_server = None
            self._default_connected = False
    
    def _get_jenkins_connection(self, jenkins_url, username=None, token=None, jenkins_service=None):
        """Get or create Jenkins connection for specific instance"""
        # Try database credentials first if no specific credentials provided
        if not username or not token:
            jenkins_creds = None
            try:
                # Try to find credentials by jenkins service name (jenkins_ltcbp, jenkins_ekp, jenkins_report)
                if jenkins_service:
                    jenkins_creds = UserData.get_credentials(jenkins_service)

                # If no specific credentials found, try default jenkins service
                if not jenkins_creds:
                    jenkins_creds = UserData.get_credentials('jenkins')
            except Exception as e:
                logger.warning(f"⚠️ Could not access database for Jenkins credentials: {e}")

            if jenkins_creds:
                auth_username = username or jenkins_creds.name or Config.JENKINS_USERNAME
                auth_token = token or jenkins_creds.token
            else:
                auth_username = username or Config.JENKINS_USERNAME
                auth_token = token or Config.JENKINS_TOKEN
        else:
            auth_username = username
            auth_token = token
        
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
                logger.error(f"Failed to connect to Jenkins {jenkins_url}: {e}")
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
        self._ensure_default_connection()
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
    
    def get_job_info(self, job_name):
        """Get job information from default Jenkins server"""
        self._ensure_default_connection()
        if not self.default_server:
            return None
        
        try:
            return self.default_server.get_job_info(job_name)
        except Exception as e:
            logger.warning(f"⚠️ Could not get job info for {job_name}: {e}")
            return None
    
    def stop_job(self, job_name, build_number=None):
        """Stop a running job"""
        self._ensure_default_connection()
        if not self.default_server:
            return False, "Default Jenkins connection not available"
        
        try:
            if build_number:
                self.default_server.stop_build(job_name, build_number)
            else:
                # Get the latest build number
                job_info = self.default_server.get_job_info(job_name)
                if job_info and 'lastBuild' in job_info and job_info['lastBuild']:
                    last_build = job_info['lastBuild']['number']
                    self.default_server.stop_build(job_name, last_build)
            
            return True, f"Job {job_name} stopped successfully"
        except Exception as e:
            return False, f"Failed to stop job: {e}"
    
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
    
    def get_job_info_with_url(self, job_name, jenkins_url=None):
        """Get job info from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            self._ensure_default_connection()
            jenkins_conn = self.default_server

        if not jenkins_conn:
            return None
        
        try:
            return jenkins_conn.get_job_info(job_name)
        except Exception as e:
            logger.error(f"Error getting job info for {job_name}: {e}")
            return None
    
    def get_build_info(self, job_name, build_number, jenkins_url=None):
        """Get build info from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            self._ensure_default_connection()
            jenkins_conn = self.default_server

        if not jenkins_conn:
            return None
        
        try:
            return jenkins_conn.get_build_info(job_name, build_number)
        except Exception as e:
            logger.error(f"Error getting build info for {job_name}#{build_number}: {e}")
            return None
    
    def list_jobs(self, jenkins_url=None):
        """List jobs from specific or default Jenkins"""
        if jenkins_url:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
        else:
            self._ensure_default_connection()
            jenkins_conn = self.default_server

        if not jenkins_conn:
            return []
        
        try:
            return jenkins_conn.get_jobs()
        except Exception as e:
            logger.error(f"Error listing Jenkins jobs: {e}")
            return []

    # Convenience methods for specific Jenkins services
    def trigger_job_ltcbp(self, job_name, parameters=None):
        """Trigger job on LTCBP Jenkins server"""
        jenkins_creds = UserData.get_credentials('jenkins_ltcbp')
        if jenkins_creds:
            jenkins_conn = self._get_jenkins_connection(
                jenkins_url=Config.JENKINS_URL,  # или URL для LTCBP
                jenkins_service='jenkins_ltcbp'
            )
            if jenkins_conn:
                try:
                    if parameters:
                        jenkins_conn.build_job(job_name, parameters)
                    else:
                        jenkins_conn.build_job(job_name)
                    return True, f"Job {job_name} triggered on LTCBP Jenkins"
                except Exception as e:
                    return False, f"Failed to trigger job on LTCBP: {e}"
        return False, "LTCBP Jenkins connection not available"

    def trigger_job_ekp(self, job_name, parameters=None):
        """Trigger job on EKP Jenkins server"""
        try:
            jenkins_conn = self._get_jenkins_connection(
                jenkins_url=Config.JENKINS_URL,  # или URL для EKP
                jenkins_service='jenkins_ekp'
            )
            if jenkins_conn:
                if parameters:
                    jenkins_conn.build_job(job_name, parameters)
                else:
                    jenkins_conn.build_job(job_name)
                return True, f"Job {job_name} triggered on EKP Jenkins"
        except Exception as e:
            return False, f"Failed to trigger job on EKP: {e}"
        return False, "EKP Jenkins connection not available"

    def trigger_job_report(self, job_name, parameters=None):
        """Trigger job on Report Jenkins server"""
        try:
            jenkins_conn = self._get_jenkins_connection(
                jenkins_url=Config.JENKINS_URL,  # или URL для Report
                jenkins_service='jenkins_report'
            )
            if jenkins_conn:
                if parameters:
                    jenkins_conn.build_job(job_name, parameters)
                else:
                    jenkins_conn.build_job(job_name)
                return True, f"Job {job_name} triggered on Report Jenkins"
        except Exception as e:
            return False, f"Failed to trigger job on Report: {e}"
        return False, "Report Jenkins connection not available"