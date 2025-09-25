from sqlalchemy import Column, Integer, String, Text
from app import db

class UserData(db.Model):
    __tablename__ = 'user_data'
    
    id = Column(Integer, primary_key=True)
    service = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    token = Column(Text, nullable=False)
    url = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f'<UserData {self.service}:{self.name}>'
    
    @classmethod
    def get_credentials(cls, service, name=None):
        """Get credentials for specific service and optionally name"""
        query = cls.query.filter_by(service=service)
        if name:
            query = query.filter_by(name=name)
        return query.first()
    
    @classmethod
    def get_service_credentials(cls, service):
        """Get all credentials for specific service"""
        return cls.query.filter_by(service=service).all()