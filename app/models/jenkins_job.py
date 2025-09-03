import os
from datetime import datetime
from app import db

class JenkinsJob(db.Model):
    __tablename__ = 'jenkins_jobs'
    
    # Use schema only for PostgreSQL
    if os.environ.get('DATABASE_URL', '').startswith('postgresql'):
        __table_args__ = {'schema': 'autoltv2'}
    else:
        __table_args__ = {}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    schedule = db.Column(db.String(100))  # Cron format
    parameters = db.Column(db.JSON)  # Job parameters
    is_active = db.Column(db.Boolean, default=True)
    
    # Execution tracking
    last_build_number = db.Column(db.Integer)
    last_build_status = db.Column(db.String(20))
    last_execution = db.Column(db.DateTime)
    next_execution = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<JenkinsJob {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schedule': self.schedule,
            'parameters': self.parameters,
            'is_active': self.is_active,
            'last_build_number': self.last_build_number,
            'last_build_status': self.last_build_status,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }