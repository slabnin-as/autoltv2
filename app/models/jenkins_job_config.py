from datetime import datetime
from app import db

class JenkinsJobConfig(db.Model):
    """
    Configuration table for Jenkins jobs across multiple instances and projects
    """
    __tablename__ = 'jenkins_job_configs'
    __table_args__ = {'schema': 'autoltv2'}
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Job identification
    job_name = db.Column(db.String(200), nullable=False, index=True)
    display_name = db.Column(db.String(200))  # Human-readable name
    project_name = db.Column(db.String(100), nullable=False, index=True)  # Project identifier
    
    # Jenkins instance configuration
    jenkins_url = db.Column(db.String(500), nullable=False)  # Full Jenkins instance URL
    job_path = db.Column(db.String(500), nullable=False)     # Path to job on Jenkins (e.g., /job/folder/job/jobname)
    
    # Authentication (optional per job override)
    username = db.Column(db.String(100))   # Override default username if needed
    api_token = db.Column(db.String(500))  # Override default API token if needed
    
    # Job configuration
    description = db.Column(db.Text)
    parameters = db.Column(db.JSON)  # Default job parameters
    environment = db.Column(db.String(50), default='production')  # dev, staging, production
    
    # Status and control
    is_active = db.Column(db.Boolean, default=True)
    is_manual_only = db.Column(db.Boolean, default=False)  # Requires manual approval
    max_concurrent_builds = db.Column(db.Integer, default=1)
    
    # Execution tracking
    last_build_number = db.Column(db.Integer)
    last_build_status = db.Column(db.String(50))
    last_execution = db.Column(db.DateTime)
    last_success = db.Column(db.DateTime)
    execution_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.String(100))  # Who added this config
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_project_active', 'project_name', 'is_active'),
        db.Index('idx_job_name_project', 'job_name', 'project_name'),
        {'schema': 'autoltv2'}
    )
    
    def __repr__(self):
        return f'<JenkinsJobConfig {self.project_name}:{self.job_name}>'
    
    @property
    def full_job_url(self):
        """Generate full URL to the Jenkins job"""
        return f"{self.jenkins_url.rstrip('/')}{self.job_path}"
    
    @property
    def build_url(self):
        """Generate URL to trigger the job"""
        return f"{self.full_job_url}/build"
    
    @property
    def build_with_parameters_url(self):
        """Generate URL to trigger job with parameters"""
        return f"{self.full_job_url}/buildWithParameters"
    
    def get_auth_credentials(self):
        """Get authentication credentials (job-specific or global fallback)"""
        from config.config import Config
        
        username = self.username if self.username else Config.JENKINS_USERNAME
        token = self.api_token if self.api_token else Config.JENKINS_TOKEN
        
        return username, token
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'display_name': self.display_name,
            'project_name': self.project_name,
            'jenkins_url': self.jenkins_url,
            'job_path': self.job_path,
            'full_job_url': self.full_job_url,
            'description': self.description,
            'parameters': self.parameters,
            'environment': self.environment,
            'is_active': self.is_active,
            'is_manual_only': self.is_manual_only,
            'max_concurrent_builds': self.max_concurrent_builds,
            'last_build_number': self.last_build_number,
            'last_build_status': self.last_build_status,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'execution_count': self.execution_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def to_dict_safe(self):
        """Safe version without sensitive data"""
        data = self.to_dict()
        # Remove sensitive information
        data.pop('username', None)
        data.pop('api_token', None)
        return data