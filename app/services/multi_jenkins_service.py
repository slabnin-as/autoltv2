from datetime import datetime
import jenkins
from app import db
from app.models.jenkins_job import JenkinsJob
from app.models.jenkins_job_config import JenkinsJobConfig
from config.config import Config

class MultiJenkinsService:
    """
    Enhanced Jenkins service supporting multiple Jenkins instances and projects
    """
    
    def __init__(self):
        self.connections = {}  # Cache of Jenkins connections
    
    def _get_jenkins_connection(self, jenkins_url, username=None, token=None):
        """
        Get or create Jenkins connection for a specific instance
        """
        # Use provided credentials or fall back to global config
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
                print(f"✅ Connected to Jenkins: {jenkins_url}")
            except Exception as e:
                print(f"❌ Failed to connect to Jenkins {jenkins_url}: {e}")
                self.connections[connection_key] = None
        
        return self.connections[connection_key]
    
    def trigger_job_by_config(self, job_config_id, parameters=None, triggered_by=None):
        """
        Trigger a Jenkins job using JenkinsJobConfig
        """
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return False, f"Job configuration {job_config_id} not found"
        
        if not job_config.is_active:
            return False, f"Job {job_config.job_name} is disabled"
        
        # Check if manual approval required
        if job_config.is_manual_only and not triggered_by:
            return False, f"Job {job_config.job_name} requires manual approval"
        
        # Get Jenkins connection for this specific instance
        username, token = job_config.get_auth_credentials()
        jenkins_conn = self._get_jenkins_connection(
            job_config.jenkins_url, 
            username, 
            token
        )
        
        if not jenkins_conn:
            return False, f"Cannot connect to Jenkins instance: {job_config.jenkins_url}"
        
        try:
            # Merge default parameters with provided ones
            job_parameters = job_config.parameters.copy() if job_config.parameters else {}
            if parameters:
                job_parameters.update(parameters)
            
            # Add metadata
            job_parameters.update({
                'TRIGGERED_BY': triggered_by or 'AutoLT System',
                'TRIGGER_TIME': datetime.now().isoformat(),
                'PROJECT_NAME': job_config.project_name
            })
            
            # Trigger the job
            if job_parameters:
                build_number = jenkins_conn.build_job(job_config.job_name, job_parameters)
            else:
                build_number = jenkins_conn.build_job(job_config.job_name)
            
            # Update job config record
            job_config.last_execution = datetime.now()
            job_config.execution_count = (job_config.execution_count or 0) + 1
            db.session.commit()
            
            # Also update legacy JenkinsJob if exists
            legacy_job = JenkinsJob.query.filter_by(name=job_config.job_name).first()
            if legacy_job:
                legacy_job.last_execution = datetime.now()
                db.session.commit()
            
            return True, {
                'message': f"Job {job_config.job_name} triggered successfully",
                'build_number': build_number,
                'jenkins_url': job_config.jenkins_url,
                'job_url': job_config.full_job_url,
                'parameters': job_parameters
            }
            
        except Exception as e:
            return False, f"Failed to trigger job {job_config.job_name}: {e}"
    
    def trigger_job_by_name(self, job_name, project_name=None, parameters=None, triggered_by=None):
        """
        Trigger job by name, optionally filtered by project
        """
        query = JenkinsJobConfig.query.filter_by(job_name=job_name, is_active=True)
        if project_name:
            query = query.filter_by(project_name=project_name)
        
        job_configs = query.all()
        
        if not job_configs:
            return False, f"No active job configuration found for '{job_name}'"
        
        if len(job_configs) > 1 and not project_name:
            projects = [config.project_name for config in job_configs]
            return False, f"Multiple jobs named '{job_name}' found in projects: {projects}. Specify project_name."
        
        return self.trigger_job_by_config(job_configs[0].id, parameters, triggered_by)
    
    def get_job_status(self, job_config_id):
        """
        Get current status of a job
        """
        job_config = JenkinsJobConfig.query.get(job_config_id)
        if not job_config:
            return None
        
        username, token = job_config.get_auth_credentials()
        jenkins_conn = self._get_jenkins_connection(
            job_config.jenkins_url, 
            username, 
            token
        )
        
        if not jenkins_conn:
            return None
        
        try:
            job_info = jenkins_conn.get_job_info(job_config.job_name)
            
            # Update job config with latest info
            if job_info and job_info.get('lastBuild'):
                last_build = job_info['lastBuild']
                build_info = jenkins_conn.get_build_info(job_config.job_name, last_build['number'])
                
                job_config.last_build_number = last_build['number']
                job_config.last_build_status = build_info.get('result', 'UNKNOWN')
                
                if build_info.get('result') == 'SUCCESS':
                    job_config.last_success = datetime.fromtimestamp(build_info['timestamp'] / 1000)
                
                db.session.commit()
            
            return {
                'job_name': job_config.job_name,
                'project_name': job_config.project_name,
                'jenkins_url': job_config.jenkins_url,
                'job_info': job_info,
                'last_build_number': job_config.last_build_number,
                'last_build_status': job_config.last_build_status,
                'last_execution': job_config.last_execution,
                'last_success': job_config.last_success
            }
            
        except Exception as e:
            print(f"Error getting job status for {job_config.job_name}: {e}")
            return None
    
    def get_jobs_by_project(self, project_name, active_only=True):
        """
        Get all job configurations for a specific project
        """
        query = JenkinsJobConfig.query.filter_by(project_name=project_name)
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(JenkinsJobConfig.job_name).all()
    
    def get_all_projects(self):
        """
        Get list of all projects with their job counts
        """
        projects = db.session.query(
            JenkinsJobConfig.project_name,
            db.func.count(JenkinsJobConfig.id).label('job_count'),
            db.func.count(db.case((JenkinsJobConfig.is_active == True, 1))).label('active_jobs')
        ).group_by(JenkinsJobConfig.project_name).all()
        
        return [
            {
                'project_name': project.project_name,
                'total_jobs': project.job_count,
                'active_jobs': project.active_jobs
            }
            for project in projects
        ]
    
    def bulk_trigger_by_project(self, project_name, parameters=None, triggered_by=None):
        """
        Trigger all active jobs in a project
        """
        job_configs = self.get_jobs_by_project(project_name, active_only=True)
        
        if not job_configs:
            return False, f"No active jobs found for project '{project_name}'"
        
        results = []
        success_count = 0
        
        for job_config in job_configs:
            success, result = self.trigger_job_by_config(job_config.id, parameters, triggered_by)
            
            results.append({
                'job_name': job_config.job_name,
                'success': success,
                'result': result
            })
            
            if success:
                success_count += 1
        
        return True, {
            'message': f"Triggered {success_count}/{len(job_configs)} jobs in project '{project_name}'",
            'results': results
        }
    
    def validate_job_config(self, job_config):
        """
        Validate a job configuration by testing connection and job existence
        """
        username, token = job_config.get_auth_credentials()
        jenkins_conn = self._get_jenkins_connection(
            job_config.jenkins_url,
            username,
            token
        )
        
        if not jenkins_conn:
            return False, f"Cannot connect to Jenkins instance: {job_config.jenkins_url}"
        
        try:
            # Check if job exists
            job_info = jenkins_conn.get_job_info(job_config.job_name)
            if not job_info:
                return False, f"Job '{job_config.job_name}' not found on Jenkins instance"
            
            return True, f"Job configuration valid. Job URL: {job_config.full_job_url}"
            
        except Exception as e:
            return False, f"Validation failed: {e}"