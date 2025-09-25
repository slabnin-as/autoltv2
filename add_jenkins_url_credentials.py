#!/usr/bin/env python3
"""
Script to add URL-specific Jenkins credentials to database
"""
import os
from app import create_app, db
from app.models.user_data import UserData
from config.config import config as app_config

def add_jenkins_url_credentials():
    """Add Jenkins credentials for specific URL"""
    print("Adding Jenkins credentials for specific URL...")

    jenkins_url = input("Enter Jenkins URL (e.g., http://jenkins.example.com): ")
    jenkins_username = input("Enter Jenkins username: ")
    jenkins_token = input("Enter Jenkins API token: ")

    # Check if credentials for this URL already exist
    existing = UserData.query.filter_by(service='jenkins', name=jenkins_url).first()
    if existing:
        print(f"Updating existing Jenkins credentials for URL: {jenkins_url}")
        existing.token = f"{jenkins_username}:{jenkins_token}"
    else:
        print(f"Creating new Jenkins credentials for URL: {jenkins_url}")
        jenkins_creds = UserData(
            service='jenkins',
            name=jenkins_url,
            token=f"{jenkins_username}:{jenkins_token}"
        )
        db.session.add(jenkins_creds)

    db.session.commit()
    print(f"✅ Jenkins credentials saved for {jenkins_url}!")

def list_jenkins_credentials():
    """List all Jenkins credentials"""
    print("\n📋 Jenkins credentials in database:")

    jenkins_creds = UserData.query.filter_by(service='jenkins').all()
    if not jenkins_creds:
        print("No Jenkins credentials found in database")
        return

    for cred in jenkins_creds:
        if ':' in cred.token:
            username, token = cred.token.split(':', 1)
            print(f"- URL: {cred.name}, Username: {username}, Token: {'***' + token[-4:] if len(token) > 4 else '***'}")
        else:
            print(f"- Name: {cred.name}, Token: {'***' + cred.token[-4:] if len(cred.token) > 4 else '***'}")

def main():
    """Main function"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])

    with app.app_context():
        print("🔐 Jenkins URL Credentials Manager")
        print("=" * 40)

        while True:
            print("\nOptions:")
            print("1. Add/Update Jenkins credentials for URL")
            print("2. List Jenkins credentials")
            print("3. Exit")

            choice = input("\nSelect option (1-3): ").strip()

            if choice == '1':
                add_jenkins_url_credentials()
            elif choice == '2':
                list_jenkins_credentials()
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice, please try again")

if __name__ == '__main__':
    main()