#!/usr/bin/env python3
"""
Script to recreate user_data table without timestamps
"""
import os
from app import create_app, db
from app.models.user_data import UserData
from config.config import config as app_config

def recreate_user_data_table():
    """Drop and recreate user_data table"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("Dropping existing user_data table...")
        with db.engine.connect() as conn:
            conn.execute(db.text('DROP TABLE IF EXISTS user_data;'))
            conn.commit()
        
        print("Creating new user_data table...")
        db.create_all()
        print("✅ user_data table recreated successfully!")
        
        # Show table info
        print("\n📊 New table structure:")
        print("- id: Integer (Primary Key)")
        print("- service: String(50) - jenkins, jira, etc.")
        print("- name: String(100) - optional username/identifier")
        print("- token: Text - API token/password")

if __name__ == '__main__':
    recreate_user_data_table()