from sqlalchemy import Column, Integer, String, DateTime
from app import db

class Scheduler(db.Model):
    __tablename__ = 'scheduler'
    
    id = Column(Integer, primary_key=True)
    jira_task = Column(String(50), nullable=False, index=True)
    planned_start = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=True)
    stage_before_start = Column(DateTime, nullable=True)
    stage_before_end = Column(DateTime, nullable=True)
    stage_deploy_start = Column(DateTime, nullable=True)
    stage_deploy_end = Column(DateTime, nullable=True)
    stage_after_start = Column(DateTime, nullable=True)
    stage_after_end = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Scheduler {self.jira_task}:{self.status}>'