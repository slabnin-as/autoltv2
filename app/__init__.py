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
    flask_env = app.config.get('FLASK_ENV', os.getenv('FLASK_ENV', 'development'))
    if flask_env == 'production':
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    
    # Create log directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging handlers
    handlers = []
    
    # Console handler for development or if no log directory
    if flask_env == 'development':
        handlers.append(logging.StreamHandler())
    
    # File handler for production
    if flask_env == 'production':
        app_log_file = os.path.join(log_dir, 'app.log')
        file_handler = logging.FileHandler(app_log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        handlers.append(file_handler)
        
        # Also log to console in production for systemd capture
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers
    )
    
    # Set specific loggers
    app.logger.setLevel(log_level)
    
    # Configure werkzeug logger (Flask's internal server)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Configure our application loggers
    logging.getLogger('app.services').setLevel(log_level)
    logging.getLogger('app.models').setLevel(log_level)
    
    app.logger.info(f"🔧 Logging configured at {logging.getLevelName(log_level)} level")
    app.logger.info(f"📁 Log directory: {log_dir}")

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
    
    # Log successful application startup
    flask_env = app.config.get('FLASK_ENV', os.getenv('FLASK_ENV', 'development'))
    app.logger.info("🚀 AutoLT v2 приложение запустилось нормально!")
    app.logger.info(f"🌐 Сервер запущен в режиме: {flask_env}")
    
    return app

from app import models