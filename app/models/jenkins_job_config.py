from app import db

class JenkinsJobConfig(db.Model):
    __tablename__ = 'jenkins_job_configs'
    __table_args__ = {'schema': 'autoltv2'}
    
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(200), nullable=False)
    job_path = db.Column(db.String(200), nullable=False)
    project = db.Column(db.String(200), nullable=False)
    project_url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    pipeline = db.Column(db.String(50), nullable=True)  # EKP, INFOSRV
    
    def __repr__(self):
        return f'<JenkinsJobConfig {self.job_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'job_path': self.job_path,
            'project': self.project,
            'project_url': self.project_url,
            'description': self.description,
            'pipeline': self.pipeline
        }