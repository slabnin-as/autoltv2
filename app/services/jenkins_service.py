import logging
import urllib3
from datetime import datetime
import jenkins
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.models.user_data import UserData
from config.config import Config

# Disable SSL warnings for Jenkins connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class JenkinsService:
    def __init__(self):
        self.connections = {}  # Cache for multiple Jenkins connections
    
    
    def _get_jenkins_connection(self, jenkins_url, username=None, token=None):
        """Get or create Jenkins connection for specific instance"""
        # Try database credentials first if no specific credentials provided
        if not username or not token:
            jenkins_creds = None
            try:
                # Ищем credentials по URL в поле url таблицы user_data
                jenkins_creds = UserData.query.filter_by(url=jenkins_url).first()

                logger.info(f"🔍 Поиск credentials для URL: {jenkins_url}")
                if jenkins_creds:
                    logger.info(f"✅ Найдены credentials: name={jenkins_creds.name}, url={jenkins_creds.url}")
                else:
                    logger.warning(f"⚠️ Не найдены Jenkins credentials для URL: {jenkins_url}")

            except Exception as e:
                logger.warning(f"⚠️ Ошибка доступа к БД для Jenkins credentials: {e}")

            if jenkins_creds:
                # Берем name как username, token как token
                auth_username = username or jenkins_creds.name
                auth_token = token or jenkins_creds.token
            else:
                # Fallback на переменные окружения
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
                # Disable SSL certificate verification
                self.connections[connection_key]._session.verify = False
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
    
    
    def get_job_info_by_url(self, job_name, jenkins_url):
        """Get job information from specific Jenkins server"""
        jenkins_conn = self._get_jenkins_connection(jenkins_url)
        if not jenkins_conn:
            return None

        try:
            return jenkins_conn.get_job_info(job_name)
        except Exception as e:
            logger.warning(f"⚠️ Could not get job info for {job_name} on {jenkins_url}: {e}")
            return None
    
    def stop_job_by_url(self, job_name, jenkins_url, build_number=None):
        """Stop a running job on specific Jenkins server"""
        jenkins_conn = self._get_jenkins_connection(jenkins_url)
        if not jenkins_conn:
            return False, f"Cannot connect to Jenkins: {jenkins_url}"

        try:
            if build_number:
                jenkins_conn.stop_build(job_name, build_number)
            else:
                # Get the latest build number
                job_info = jenkins_conn.get_job_info(job_name)
                if job_info and 'lastBuild' in job_info and job_info['lastBuild']:
                    last_build = job_info['lastBuild']['number']
                    jenkins_conn.stop_build(job_name, last_build)

            return True, f"Job {job_name} stopped successfully on {jenkins_url}"
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
    
    def get_job_info_with_url(self, job_name, jenkins_url):
        """Get job info from specific Jenkins"""
        jenkins_conn = self._get_jenkins_connection(jenkins_url)
        if not jenkins_conn:
            return None

        try:
            return jenkins_conn.get_job_info(job_name)
        except Exception as e:
            logger.error(f"Error getting job info for {job_name}: {e}")
            return None
    
    def get_build_info(self, job_name, build_number, jenkins_url):
        """Get build info from specific Jenkins"""
        jenkins_conn = self._get_jenkins_connection(jenkins_url)
        if not jenkins_conn:
            return None

        try:
            return jenkins_conn.get_build_info(job_name, build_number)
        except Exception as e:
            logger.error(f"Error getting build info for {job_name}#{build_number}: {e}")
            return None
    
    def list_jobs(self, jenkins_url):
        """List jobs from specific Jenkins"""
        jenkins_conn = self._get_jenkins_connection(jenkins_url)
        if not jenkins_conn:
            return []

        try:
            return jenkins_conn.get_jobs()
        except Exception as e:
            logger.error(f"Error listing Jenkins jobs: {e}")
            return []

    # Convenience methods for different Jenkins URLs
    def trigger_job_by_url(self, jenkins_url, job_name, parameters=None):
        """Trigger job on specific Jenkins server by URL"""
        try:
            jenkins_conn = self._get_jenkins_connection(jenkins_url)
            if jenkins_conn:
                if parameters:
                    jenkins_conn.build_job(job_name, parameters)
                else:
                    jenkins_conn.build_job(job_name)
                return True, f"Job {job_name} triggered on {jenkins_url}"
        except Exception as e:
            return False, f"Failed to trigger job on {jenkins_url}: {e}"
        return False, f"Jenkins connection not available for {jenkins_url}"