import os
from app import create_app, db
from app.models import JiraTask, JenkinsJob, JenkinsJobConfig
from config.config import config
from app.services.scheduler_service import SchedulerService

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config[config_name])

# Initialize scheduler
scheduler_service = SchedulerService()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'JiraTask': JiraTask,
        'JenkinsJob': JenkinsJob,
        'JenkinsJobConfig': JenkinsJobConfig,
        'scheduler': scheduler_service
    }

# with app.app_context():
#     scheduler_service.update_job_schedules()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)