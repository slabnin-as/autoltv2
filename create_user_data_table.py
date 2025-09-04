#!/usr/bin/env python3
"""
Script to create user_data table directly
"""
import os
from app import create_app, db
from app.models.user_data import UserData
from config.config import config as app_config

def create_user_data_table():
    """Create user_data table"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("Creating user_data table...")
        db.create_all()
        print("✅ user_data table created successfully!")
        
        # Show table info
        print("\n📊 Table structure:")
        print("- id: Integer (Primary Key)")
        print("- service: String(50) - jenkins, jira, etc.")
        print("- name: String(100) - optional username/identifier")
        print("- token: Text - API token/password")
        print("- created_at: DateTime")
        print("- updated_at: DateTime")

if __name__ == '__main__':
    create_user_data_table()