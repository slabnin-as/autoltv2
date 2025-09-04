#!/usr/bin/env python3
"""
Script to populate jenkins_job_configs table with simple test data
"""
import os
from app import create_app, db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.services.multi_jenkins_service import MultiJenkinsService
from config.config import config as app_config

def create_jenkins_test_configs():
    """Create simple Jenkins job configurations"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        # Clear existing configs
        print("🗑️  Clearing existing configs...")
        JenkinsJobConfig.query.delete()
        db.session.commit()
        
        # Test Jenkins connectivity 
        jenkins_service = MultiJenkinsService()
        
        # Create simple job configurations
        print("📝 Creating job configurations...")
        job_configs = []
        
        # EKPLT Project Jobs
        job_configs.append(JenkinsJobConfig(
            job_name='deploy-production-ekplt',
            job_path='/job/EKPLT/job/deploy-production-ekplt',
            project='EKPLT',
            project_url='https://jenkins-prod.company.ru',
            description='Автоматическое развертывание EKPLT в production среде'
        ))
        
        job_configs.append(JenkinsJobConfig(
            job_name='backup-ekplt-database',
            job_path='/job/EKPLT/job/backup-ekplt-database',
            project='EKPLT',
            project_url='https://jenkins-prod.company.ru',
            description='Создание бэкапа базы данных EKPLT'
        ))
        
        job_configs.append(JenkinsJobConfig(
            job_name='monitor-ekplt-health',
            job_path='/job/monitoring/job/monitor-ekplt-health',
            project='EKPLT',
            project_url='https://jenkins-monitoring.company.ru',
            description='Проверка работоспособности системы EKPLT'
        ))
        
        # MOBILE Project Jobs
        job_configs.append(JenkinsJobConfig(
            job_name='build-mobile-android',
            job_path='/job/mobile/job/build-mobile-android',
            project='MOBILE',
            project_url='https://jenkins-mobile.company.ru',
            description='Сборка Android приложения'
        ))
        
        job_configs.append(JenkinsJobConfig(
            job_name='build-mobile-ios',
            job_path='/job/mobile/job/build-mobile-ios',
            project='MOBILE',
            project_url='https://jenkins-mobile.company.ru',
            description='Сборка iOS приложения'
        ))
        
        job_configs.append(JenkinsJobConfig(
            job_name='test-mobile-integration',
            job_path='/job/mobile/job/test-mobile-integration',
            project='MOBILE',
            project_url='https://jenkins-mobile.company.ru',
            description='Интеграционные тесты для мобильных приложений'
        ))
        
        # ANALYTICS Project Jobs
        job_configs.append(JenkinsJobConfig(
            job_name='process-analytics-data',
            job_path='/job/analytics/job/process-analytics-data',
            project='ANALYTICS',
            project_url='https://jenkins-data.company.ru',
            description='Обработка и агрегация данных аналитики'
        ))
        
        job_configs.append(JenkinsJobConfig(
            job_name='generate-weekly-reports',
            job_path='/job/analytics/job/generate-weekly-reports',
            project='ANALYTICS',
            project_url='https://jenkins-data.company.ru',
            description='Генерация еженедельных аналитических отчетов'
        ))
        
        # Add all configurations to database
        for i, config in enumerate(job_configs, 1):
            db.session.add(config)
            print(f"    {i}. {config.project}:{config.job_name}")
        
        db.session.commit()
        print(f"\n✅ Successfully created {len(job_configs)} job configurations")

def show_configs_summary():
    """Show summary of created configurations"""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        print("\n📊 Jenkins Configurations Summary")
        print("=" * 40)
        
        total_configs = JenkinsJobConfig.query.count()
        print(f"📋 Total configurations: {total_configs}")
        
        print("\n📊 By Project:")
        projects = db.session.query(
            JenkinsJobConfig.project,
            db.func.count(JenkinsJobConfig.id).label('total')
        ).group_by(JenkinsJobConfig.project).all()
        
        for project in projects:
            print(f"   🎯 {project.project}: {project.total} jobs")
        
        print("\n🔧 By Project URL:")
        urls = db.session.query(
            JenkinsJobConfig.project_url,
            db.func.count(JenkinsJobConfig.id).label('job_count')
        ).group_by(JenkinsJobConfig.project_url).all()
        
        for url in urls:
            print(f"   🏠 {url.project_url}: {url.job_count} jobs")

if __name__ == '__main__':
    print("🔧 Jenkins Job Configurations Test Data Generator")
    print("=" * 50)
    
    # Test Jenkins connection first (will show error but continue)
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(app_config[config_name])
    
    with app.app_context():
        jenkins_service = MultiJenkinsService()
    
    # Create test configurations
    create_jenkins_test_configs()
    show_configs_summary()
    
    print("\n🎉 Jenkins configurations created!")
    print("\n💡 Available endpoints:")
    print("   📋 List configs: http://localhost:5000/jenkins-configs/")
    print("   🔧 API configs: http://localhost:5000/jenkins-configs/api/configs")
    print("   📊 API projects: http://localhost:5000/jenkins-configs/api/projects")
    
    print("\n💻 Example API calls:")
    print("   curl http://localhost:5000/jenkins-configs/api/configs?project=EKPLT")
    print("   curl -X POST http://localhost:5000/jenkins-configs/api/trigger/1")