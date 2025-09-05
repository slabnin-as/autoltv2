#!/usr/bin/env python3
"""
Local script to create scheduler table
"""
import os
from app import create_app, db
from app.models.scheduler import Scheduler
from config.config import config as app_config

def create_scheduler_table():
    """Create scheduler table"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("Creating scheduler table...")
        db.create_all()
        print("✅ scheduler table created successfully!")
        
        print("\n📊 Table structure:")
        print("- id: Integer (Primary Key)")
        print("- jira_task: String(50) - JIRA task key")
        print("- planned_start: DateTime")
        print("- status: String(20)")
        print("- stage_before_start: DateTime")
        print("- stage_before_end: DateTime")
        print("- stage_deploy_start: DateTime")
        print("- stage_deploy_end: DateTime")
        print("- stage_after_start: DateTime")
        print("- stage_after_end: DateTime")

if __name__ == '__main__':
    create_scheduler_table()