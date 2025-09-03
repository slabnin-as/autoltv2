import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:example@192.168.1.8:5432/de_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database engine options for schema
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'options': '-csearch_path=autoltv2,public'
        }
    }
    
    # Jira Configuration
    JIRA_URL = os.environ.get('JIRA_URL')
    JIRA_USERNAME = os.environ.get('JIRA_USERNAME')
    JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')
    
    # Jenkins Configuration
    JENKINS_URL = os.environ.get('JENKINS_URL')
    JENKINS_USERNAME = os.environ.get('JENKINS_USERNAME')
    JENKINS_TOKEN = os.environ.get('JENKINS_TOKEN')
    
    # Redis for Celery and Caching
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Scheduler Configuration
    SCHEDULER_API_ENABLED = True
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///autoltv2.db'
    
    # Override schema options for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {}

class ProductionConfig(Config):
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://username:password@localhost/autoltv2_test'
    WTF_CSRF_ENABLED = False
    
    # Database engine options for schema
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'options': '-csearch_path=autoltv2,public'
        }
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}