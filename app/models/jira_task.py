import os
from datetime import datetime
from app import db

class JiraTask(db.Model):
    __tablename__ = 'jira_tasks'
    
    # Use schema only for PostgreSQL
    if os.environ.get('DATABASE_URL', '').startswith('postgresql'):
        __table_args__ = {'schema': 'autoltv2'}
    else:
        __table_args__ = {}
    
    id = db.Column(db.Integer, primary_key=True)
    jira_key = db.Column(db.String(20), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False)
    assignee = db.Column(db.String(100))
    reporter = db.Column(db.String(100))
    priority = db.Column(db.String(20))
    issue_type = db.Column(db.String(50))
    project_key = db.Column(db.String(10), nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime)
    updated_date = db.Column(db.DateTime)
    resolved_date = db.Column(db.DateTime)
    
    # Metadata
    last_synced = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<JiraTask {self.jira_key}: {self.summary}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'jira_key': self.jira_key,
            'summary': self.summary,
            'description': self.description,
            'status': self.status,
            'assignee': self.assignee,
            'reporter': self.reporter,
            'priority': self.priority,
            'issue_type': self.issue_type,
            'project_key': self.project_key,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None
        }