#!/usr/bin/env python3
"""
Health check script for AutoLT v2
"""
import os
import requests
import sys
from datetime import datetime

def check_app_health(base_url="http://localhost:5000"):
    """Check if application is running and responding"""
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Application is running")
            return True
        else:
            print(f"❌ Application returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Application is not accessible: {e}")
        return False

def check_api_endpoints(base_url="http://localhost:5000"):
    """Check API endpoints"""
    endpoints = [
        "/tasks/api/scheduling-status",
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
                all_ok = False
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")
            all_ok = False
    
    return all_ok

def check_environment():
    """Check environment configuration"""
    required_vars = [
        'SECRET_KEY', 'DATABASE_URL', 'JIRA_URL', 
        'JIRA_USERNAME', 'JIRA_API_TOKEN',
        'JENKINS_URL', 'JENKINS_USERNAME', 'JENKINS_TOKEN'
    ]
    
    all_set = True
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} - Set")
        else:
            print(f"❌ {var} - Missing")
            all_set = False
    
    return all_set

def main():
    """Run health checks"""
    print(f"🏥 AutoLT v2 Health Check - {datetime.now()}")
    print("=" * 50)
    
    print("\n📋 Environment Variables:")
    env_ok = check_environment()
    
    print("\n🌐 Application Health:")
    app_ok = check_app_health()
    
    print("\n🔌 API Endpoints:")
    api_ok = check_api_endpoints()
    
    print("\n" + "=" * 50)
    if env_ok and app_ok and api_ok:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()