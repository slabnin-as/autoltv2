#!/usr/bin/env python3
"""
Script to add service credentials to database
"""
import os
from app import create_app, db
from app.models.user_data import UserData
from config.config import config as app_config

def add_jira_credentials():
    """Add JIRA credentials to database"""
    print("Adding JIRA credentials to database...")
    
    jira_username = input("Enter JIRA username/email: ")
    jira_token = input("Enter JIRA API token: ")
    
    # Check if JIRA credentials already exist
    existing = UserData.get_credentials('jira')
    if existing:
        print(f"Updating existing JIRA credentials for user: {existing.name}")
        existing.name = jira_username
        existing.token = jira_token
    else:
        print("Creating new JIRA credentials")
        jira_creds = UserData(
            service='jira',
            name=jira_username,
            token=jira_token
        )
        db.session.add(jira_creds)
    
    db.session.commit()
    print("✅ JIRA credentials saved to database!")

def add_jenkins_credentials():
    """Add Jenkins credentials to database"""
    print("Adding Jenkins credentials to database...")
    
    jenkins_username = input("Enter Jenkins username: ")
    jenkins_token = input("Enter Jenkins API token: ")
    
    # Check if Jenkins credentials already exist
    existing = UserData.get_credentials('jenkins')
    if existing:
        print(f"Updating existing Jenkins credentials for user: {existing.name}")
        existing.name = jenkins_username
        existing.token = jenkins_token
    else:
        print("Creating new Jenkins credentials")
        jenkins_creds = UserData(
            service='jenkins',
            name=jenkins_username,
            token=jenkins_token
        )
        db.session.add(jenkins_creds)
    
    db.session.commit()
    print("✅ Jenkins credentials saved to database!")

def list_credentials():
    """List all stored credentials"""
    print("\n📋 Current credentials in database:")
    
    all_creds = UserData.query.all()
    if not all_creds:
        print("No credentials found in database")
        return
    
    for cred in all_creds:
        print(f"- Service: {cred.service}, User: {cred.name or 'N/A'}, Token: {'***' + cred.token[-4:] if len(cred.token) > 4 else '***'}")

def main():
    """Main function"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("🔐 AutoLT v2 Credentials Manager")
        print("=" * 40)
        
        while True:
            print("\nOptions:")
            print("1. Add/Update JIRA credentials")
            print("2. Add/Update Jenkins credentials")
            print("3. List all credentials")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                add_jira_credentials()
            elif choice == '2':
                add_jenkins_credentials()
            elif choice == '3':
                list_credentials()
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice, please try again")

if __name__ == '__main__':
    main()