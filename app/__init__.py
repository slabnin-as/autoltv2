from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import Config
import logging
import os

db = SQLAlchemy()
migrate = Migrate()

def setup_logging(app):
    """Configure application logging"""
    # Set logging level based on environment
    if app.config['FLASK_ENV'] == 'production':
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
        ]
    )
    
    # Set specific loggers
    app.logger.setLevel(log_level)
    
    # Configure werkzeug logger (Flask's internal server)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Configure our application loggers
    logging.getLogger('app.services').setLevel(log_level)
    logging.getLogger('app.models').setLevel(log_level)
    
    app.logger.info(f"🔧 Logging configured at {logging.getLevelName(log_level)} level")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging first
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.blueprints.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    from app.blueprints.jobs import bp as jobs_bp
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    
    
    return app

from app import models