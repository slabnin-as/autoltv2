#!/usr/bin/env python3
"""
Script to populate jenkins_job_configs table with realistic test data
"""
import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models.jenkins_job_config import JenkinsJobConfig
from config.config import config as app_config

def create_jenkins_test_configs():
    """Create realistic Jenkins job configurations"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("🔧 Creating Jenkins Job Configurations")
        print("=" * 40)
        
        # Clear existing test data
        print("🗑️  Clearing existing configs...")
        JenkinsJobConfig.query.delete()
        db.session.commit()
        
        # Define test job configurations
        job_configs = [
            # EKPLT Project - Production Jenkins
            {
                'job_name': 'deploy-production-ekplt',
                'display_name': 'Deploy EKPLT Production',
                'project_name': 'EKPLT',
                'jenkins_url': 'https://jenkins-prod.company.ru',
                'job_path': '/job/EKPLT/job/deploy-production-ekplt',
                'description': 'Автоматическое развертывание EKPLT в production среде',
                'parameters': {
                    'BRANCH': 'master',
                    'ENVIRONMENT': 'production',
                    'NOTIFICATION_CHANNELS': '#ekplt-alerts',
                    'ROLLBACK_ENABLED': True
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': True,  # Production requires approval
                'max_concurrent_builds': 1,
                'created_by': 'DevOps Team'
            },
            {
                'job_name': 'backup-ekplt-database',
                'display_name': 'Backup EKPLT Database',
                'project_name': 'EKPLT',
                'jenkins_url': 'https://jenkins-prod.company.ru',
                'job_path': '/job/EKPLT/job/backup-ekplt-database',
                'description': 'Создание бэкапа базы данных EKPLT с проверкой целостности',
                'parameters': {
                    'BACKUP_TYPE': 'full',
                    'RETENTION_DAYS': 30,
                    'COMPRESS': True,
                    'VERIFY_BACKUP': True
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': False,
                'max_concurrent_builds': 1,
                'execution_count': 15,
                'last_build_number': 47,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(hours=2),
                'last_success': datetime.now() - timedelta(hours=2),
                'created_by': 'Database Team'
            },
            {
                'job_name': 'monitor-ekplt-health',
                'display_name': 'Monitor EKPLT Health',
                'project_name': 'EKPLT',
                'jenkins_url': 'https://jenkins-monitoring.company.ru',
                'job_path': '/job/monitoring/job/monitor-ekplt-health',
                'description': 'Проверка работоспособности системы EKPLT и отправка алертов',
                'parameters': {
                    'CHECK_ENDPOINTS': True,
                    'CHECK_DATABASE': True,
                    'CHECK_SERVICES': True,
                    'ALERT_THRESHOLD': 'critical'
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': False,
                'max_concurrent_builds': 3,
                'execution_count': 240,
                'last_build_number': 1205,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(minutes=15),
                'last_success': datetime.now() - timedelta(minutes=15),
                'created_by': 'Monitoring Team'
            },
            
            # Mobile Project - Different Jenkins Instance
            {
                'job_name': 'build-mobile-android',
                'display_name': 'Build Android App',
                'project_name': 'MOBILE',
                'jenkins_url': 'https://jenkins-mobile.company.ru',
                'job_path': '/job/mobile/job/android/job/build-mobile-android',
                'description': 'Сборка Android версии мобильного приложения',
                'parameters': {
                    'BUILD_TYPE': 'release',
                    'TARGET_SDK': 34,
                    'SIGNING_KEY': 'production',
                    'PUBLISH_PLAYSTORE': False
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': False,
                'max_concurrent_builds': 2,
                'execution_count': 89,
                'last_build_number': 156,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(hours=6),
                'last_success': datetime.now() - timedelta(hours=6),
                'created_by': 'Mobile Team'
            },
            {
                'job_name': 'build-mobile-ios',
                'display_name': 'Build iOS App',
                'project_name': 'MOBILE',
                'jenkins_url': 'https://jenkins-mobile.company.ru',
                'job_path': '/job/mobile/job/ios/job/build-mobile-ios',
                'description': 'Сборка iOS версии мобильного приложения',
                'parameters': {
                    'XCODE_VERSION': '15.2',
                    'BUILD_CONFIGURATION': 'Release',
                    'PROVISIONING_PROFILE': 'distribution',
                    'UPLOAD_TESTFLIGHT': False
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': True,  # iOS builds require approval
                'max_concurrent_builds': 1,
                'execution_count': 67,
                'last_build_number': 134,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(hours=8),
                'last_success': datetime.now() - timedelta(hours=8),
                'created_by': 'Mobile Team'
            },
            {
                'job_name': 'test-mobile-integration',
                'display_name': 'Mobile Integration Tests',
                'project_name': 'MOBILE',
                'jenkins_url': 'https://jenkins-mobile.company.ru',
                'job_path': '/job/mobile/job/tests/job/test-mobile-integration',
                'description': 'Запуск интеграционных тестов мобильного приложения',
                'parameters': {
                    'TEST_ENVIRONMENT': 'staging',
                    'PARALLEL_TESTS': 4,
                    'GENERATE_REPORT': True,
                    'NOTIFY_TEAM': True
                },
                'environment': 'staging',
                'is_active': True,
                'is_manual_only': False,
                'max_concurrent_builds': 2,
                'execution_count': 156,
                'last_build_number': 298,
                'last_build_status': 'FAILURE',
                'last_execution': datetime.now() - timedelta(hours=1),
                'last_success': datetime.now() - timedelta(hours=4),
                'created_by': 'QA Team'
            },
            
            # Analytics Project - Third Jenkins Instance  
            {
                'job_name': 'process-analytics-data',
                'display_name': 'Process Analytics Data',
                'project_name': 'ANALYTICS',
                'jenkins_url': 'https://jenkins-data.company.ru',
                'job_path': '/job/analytics/job/process-analytics-data',
                'description': 'Обработка и агрегация данных аналитики',
                'parameters': {
                    'DATA_SOURCE': 'clickhouse',
                    'PROCESSING_MODE': 'incremental',
                    'OUTPUT_FORMAT': 'parquet',
                    'NOTIFICATION_EMAIL': 'analytics-team@company.ru'
                },
                'environment': 'production',
                'is_active': True,
                'is_manual_only': False,
                'max_concurrent_builds': 1,
                'execution_count': 450,
                'last_build_number': 892,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(minutes=30),
                'last_success': datetime.now() - timedelta(minutes=30),
                'created_by': 'Data Team'
            },
            {
                'job_name': 'generate-weekly-reports',
                'display_name': 'Generate Weekly Reports',
                'project_name': 'ANALYTICS',
                'jenkins_url': 'https://jenkins-data.company.ru',
                'job_path': '/job/analytics/job/reports/job/generate-weekly-reports',
                'description': 'Генерация еженедельных отчетов для руководства',
                'parameters': {
                    'REPORT_PERIOD': 'week',
                    'INCLUDE_CHARTS': True,
                    'EMAIL_RECIPIENTS': 'management@company.ru',
                    'FORMAT': 'pdf'
                },
                'environment': 'production',
                'is_active': False,  # Disabled job
                'is_manual_only': True,
                'max_concurrent_builds': 1,
                'execution_count': 52,
                'last_build_number': 67,
                'last_build_status': 'SUCCESS',
                'last_execution': datetime.now() - timedelta(days=7),
                'last_success': datetime.now() - timedelta(days=7),
                'created_by': 'Analytics Team'
            }
        ]
        
        # Insert configurations
        print("📝 Creating job configurations...")
        for i, config_data in enumerate(job_configs, 1):
            config = JenkinsJobConfig(**config_data)
            db.session.add(config)
            print(f"   {i:2d}. {config_data['project_name']}:{config_data['job_name']}")
        
        db.session.commit()
        
        print(f"\n✅ Successfully created {len(job_configs)} job configurations")
        
        return job_configs

def show_configs_summary():
    """Show summary of created configurations"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("\n📊 Jenkins Configurations Summary")
        print("=" * 40)
        
        # Total configs
        total_configs = JenkinsJobConfig.query.count()
        active_configs = JenkinsJobConfig.query.filter_by(is_active=True).count()
        print(f"📋 Total configurations: {total_configs}")
        print(f"✅ Active configurations: {active_configs}")
        print(f"❌ Disabled configurations: {total_configs - active_configs}")
        
        # By project
        print("\n📊 By Project:")
        projects = db.session.query(
            JenkinsJobConfig.project_name,
            db.func.count(JenkinsJobConfig.id).label('total'),
            db.func.count(db.case((JenkinsJobConfig.is_active == True, 1))).label('active')
        ).group_by(JenkinsJobConfig.project_name).all()
        
        for project in projects:
            print(f"   🎯 {project.project_name}: {project.active}/{project.total} active")
        
        # By Jenkins instance
        print("\n🔧 By Jenkins Instance:")
        instances = db.session.query(
            JenkinsJobConfig.jenkins_url,
            db.func.count(JenkinsJobConfig.id).label('job_count')
        ).group_by(JenkinsJobConfig.jenkins_url).all()
        
        for instance in instances:
            print(f"   🏠 {instance.jenkins_url}: {instance.job_count} jobs")
        
        # Manual approval jobs
        manual_jobs = JenkinsJobConfig.query.filter_by(is_manual_only=True, is_active=True).all()
        print(f"\n🔒 Manual approval required: {len(manual_jobs)} jobs")
        for job in manual_jobs:
            print(f"   ⚠️  {job.project_name}:{job.job_name}")

if __name__ == '__main__':
    print("🔧 Jenkins Job Configurations Test Data Generator")
    print("=" * 50)
    
    # Create test configurations
    job_configs = create_jenkins_test_configs()
    
    # Show summary
    show_configs_summary()
    
    print("\n🎉 Jenkins configurations created!")
    print("\n💡 Available endpoints:")
    print("   📋 List configs: http://localhost:5000/jenkins-configs/")
    print("   🔧 API configs: http://localhost:5000/jenkins-configs/api/configs")
    print("   📊 API projects: http://localhost:5000/jenkins-configs/api/projects")
    print("\n💻 Example API calls:")
    print("   curl http://localhost:5000/jenkins-configs/api/configs?project=EKPLT")
    print("   curl -X POST http://localhost:5000/jenkins-configs/api/trigger/1")
    print("   curl -X POST http://localhost:5000/jenkins-configs/api/trigger-project/MOBILE")