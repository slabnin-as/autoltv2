from flask import Blueprint, render_template, request, jsonify
from app.models.jira_task import JiraTask
from app.models.jenkins_job_config import JenkinsJobConfig

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    tasks_count = JiraTask.query.count()
    jobs_count = JenkinsJobConfig.query.count()
    recent_tasks = JiraTask.query.order_by(JiraTask.last_synced.desc()).limit(5).all()
    
    return render_template('index.html', 
                         tasks_count=tasks_count,
                         jobs_count=jobs_count,
                         recent_tasks=recent_tasks)

@bp.route('/api/stats')
def api_stats():
    stats = {
        'total_tasks': JiraTask.query.count(),
        'total_jobs': JenkinsJobConfig.query.count(),
        'task_statuses': {}
    }
    
    # Get task status distribution
    from sqlalchemy import func
    status_counts = JiraTask.query.with_entities(
        JiraTask.status,
        func.count(JiraTask.id)
    ).group_by(JiraTask.status).all()
    
    for status, count in status_counts:
        stats['task_statuses'][status] = count
    
    return jsonify(stats)