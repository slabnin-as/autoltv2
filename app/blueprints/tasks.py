from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import or_
from app import db
from app.models.jira_task import JiraTask
from app.services.jira_service import JiraService
from app.services.task_scheduler_service import TaskSchedulerService
from app.services.auto_task_service import AutoTaskService
from app.services.autolt_service import AutoLTService

bp = Blueprint('tasks', __name__)

@bp.route('/')
def list_tasks():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = JiraTask.query
    
    if search:
        query = query.filter(or_(
            JiraTask.jira_key.contains(search),
            JiraTask.summary.contains(search),
            JiraTask.assignee.contains(search)
        ))
    
    if status:
        query = query.filter(JiraTask.status == status)
    
    tasks = query.order_by(JiraTask.updated_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique statuses for filter
    statuses = db.session.query(JiraTask.status).distinct().all()
    statuses = [s[0] for s in statuses]
    
    return render_template('tasks/list.html', 
                         tasks=tasks, 
                         search=search,
                         current_status=status,
                         statuses=statuses)

@bp.route('/<int:task_id>')
def task_detail(task_id):
    task = JiraTask.query.get_or_404(task_id)
    return render_template('tasks/detail.html', task=task)

@bp.route('/sync', methods=['POST'])
def sync_tasks():
    jql = request.form.get('jql', 'project = "YOUR_PROJECT" AND status != "Closed"')
    max_results = request.form.get('max_results', 50, type=int)
    
    jira_service = JiraService()
    synced_count = jira_service.sync_tasks_to_db(jql, max_results)
    
    if synced_count > 0:
        flash(f'Синхронизировано {synced_count} задач из Jira', 'success')
    else:
        flash('Не удалось синхронизировать задачи', 'error')
    
    return redirect(url_for('tasks.list_tasks'))

@bp.route('/sync-ekplt', methods=['POST', 'GET'])
def sync_ekplt_tasks():
    """Sync EKPLT tasks with autolt label and planned_start >= today"""
    max_results = request.form.get('max_results', 100, type=int)
    
    jira_service = JiraService()
    synced_count = jira_service.sync_ekplt_autolt_tasks(max_results)
    
    if synced_count > 0:
        flash(f'Синхронизировано {synced_count} задач EKPLT с меткой "autolt"', 'success')
    else:
        flash('Не удалось синхронизировать задачи EKPLT или задачи не найдены', 'warning')
    
    return redirect(url_for('tasks.list_tasks'))

@bp.route('/api/sync-ekplt', methods=['POST'])
def api_sync_ekplt_tasks():
    """API endpoint for EKPLT task synchronization"""
    max_results = request.json.get('max_results', 100) if request.json else 100
    
    jira_service = JiraService()
    synced_count = jira_service.sync_ekplt_autolt_tasks(max_results)
    
    return jsonify({
        'success': synced_count > 0,
        'synced_count': synced_count,
        'message': f'Синхронизировано {synced_count} задач EKPLT' if synced_count > 0 
                  else 'Задачи не найдены или произошла ошибка'
    })

@bp.route('/api/tasks')
def api_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = JiraTask.query
    
    if search:
        query = query.filter(or_(
            JiraTask.jira_key.contains(search),
            JiraTask.summary.contains(search)
        ))
    
    tasks = query.order_by(JiraTask.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks.items],
        'total': tasks.total,
        'pages': tasks.pages,
        'current_page': page
    })

@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    task = JiraTask.query.get_or_404(task_id)
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = ['summary', 'description', 'assignee', 'priority']
    for field in allowed_fields:
        if field in data:
            setattr(task, field, data[field])
    
    db.session.commit()
    return jsonify(task.to_dict())

@bp.route('/schedule-tasks', methods=['POST'])
def schedule_tasks():
    """Schedule open tasks in available time slots"""
    scheduler = TaskSchedulerService()
    result = scheduler.schedule_next_tasks()
    
    flash(result['message'], 'success' if result['scheduled'] > 0 else 'info')
    return redirect(url_for('tasks.list_tasks'))

@bp.route('/api/schedule-tasks', methods=['POST'])
def api_schedule_tasks():
    """API endpoint for task scheduling"""
    scheduler = TaskSchedulerService()
    result = scheduler.schedule_next_tasks()
    return jsonify(result)

@bp.route('/api/scheduling-status')
def api_scheduling_status():
    """API endpoint to get scheduling status"""
    scheduler = TaskSchedulerService()
    status = scheduler.get_scheduling_status()
    return jsonify(status)

@bp.route('/api/auto-sync-and-schedule', methods=['POST'])
def api_auto_sync_and_schedule():
    """API endpoint for automated sync and scheduling (for cron)"""
    auto_service = AutoTaskService()
    result = auto_service.sync_and_schedule_tasks()
    return jsonify(result)

@bp.route('/api/auto-sync-only', methods=['POST'])
def api_auto_sync_only():
    """API endpoint for sync only (for cron)"""
    auto_service = AutoTaskService()
    result = auto_service.sync_tasks_only()
    return jsonify(result)

@bp.route('/api/autolt-process', methods=['POST'])
def api_autolt_process():
    """API endpoint for AutoLT process execution (for cron)"""
    autolt_service = AutoLTService()
    result = autolt_service.run_autolt_process()
    return jsonify(result)

@bp.route('/api/auto-schedule-only', methods=['POST'])
def api_auto_schedule_only():
    """API endpoint for scheduling only (for cron)"""
    auto_service = AutoTaskService()
    result = auto_service.schedule_tasks_only()
    return jsonify(result)