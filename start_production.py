#!/usr/bin/env python3
"""
Production startup script for AutoLT v2
"""
import os
import sys
from app import create_app, db
from config.config import Config

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'JIRA_URL',
        'JIRA_USERNAME', 
        'JIRA_API_TOKEN',
        'JENKINS_URL',
        'JENKINS_USERNAME',
        'JENKINS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in .env file or environment")
        return False
    
    return True

def initialize_database():
    """Initialize database tables"""
    try:
        print("🔄 Initializing database...")
        app = create_app(Config)
        
        with app.app_context():
            # Import all models to ensure they're registered
            from app.models import JiraTask, JenkinsJobConfig, UserData, Scheduler
            
            # Create all tables
            db.create_all()
            print("✅ Database initialized successfully!")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 AutoLT v2 Production Setup")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    print("\n✅ Production setup completed!")
    print("\nNext steps:")
    print("1. Start with: gunicorn -c gunicorn.conf.py run:app")
    print("2. Or use supervisor/systemd for production")
    print("3. Set up nginx reverse proxy")
    print("4. Configure cron for automation")

if __name__ == '__main__':
    main()