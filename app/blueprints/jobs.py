from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.services.jenkins_service import JenkinsService
from app.services.scheduler_service import SchedulerService

bp = Blueprint('jobs', __name__)

scheduler_service = SchedulerService()

@bp.route('/')
def list_jobs():
    page = request.args.get('page', 1, type=int)
    jobs = JenkinsJob.query.order_by(JenkinsJob.updated_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('jobs/list.html', jobs=jobs)

@bp.route('/<int:job_id>')
def job_detail(job_id):
    job = JenkinsJob.query.get_or_404(job_id)
    return render_template('jobs/detail.html', job=job)

@bp.route('/create', methods=['GET', 'POST'])
def create_job():
    if request.method == 'POST':
        job = JenkinsJob(
            name=request.form['name'],
            description=request.form.get('description', ''),
            schedule=request.form.get('schedule', ''),
            parameters=request.form.get('parameters', {}),
            is_active=bool(request.form.get('is_active'))
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Schedule the job if it has a schedule
        if job.schedule and job.is_active:
            job_id = f"jenkins_{job.id}"
            success, message = scheduler_service.add_scheduled_job(
                job_id, job.schedule, job.name, job.parameters
            )
            if not success:
                flash(f'Работа создана, но не удалось запланировать: {message}', 'warning')
            else:
                flash('Работа успешно создана и запланирована', 'success')
        else:
            flash('Работа успешно создана', 'success')
        
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('jobs/create.html')

@bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    job = JenkinsJob.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.name = request.form['name']
        job.description = request.form.get('description', '')
        job.schedule = request.form.get('schedule', '')
        job.is_active = bool(request.form.get('is_active'))
        
        db.session.commit()
        
        # Update schedule
        scheduler_job_id = f"jenkins_{job.id}"
        scheduler_service.remove_scheduled_job(scheduler_job_id)
        
        if job.schedule and job.is_active:
            success, message = scheduler_service.add_scheduled_job(
                scheduler_job_id, job.schedule, job.name, job.parameters
            )
            if not success:
                flash(f'Работа обновлена, но не удалось перепланировать: {message}', 'warning')
        
        flash('Работа успешно обновлена', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('jobs/edit.html', job=job)

@bp.route('/<int:job_id>/trigger', methods=['POST'])
def trigger_job(job_id):
    job = JenkinsJob.query.get_or_404(job_id)
    jenkins_service = JenkinsService()
    
    success, message = jenkins_service.trigger_job(job.name, job.parameters)
    
    if success:
        flash(f'Работа {job.name} успешно запущена', 'success')
    else:
        flash(f'Не удалось запустить работу: {message}', 'error')
    
    return redirect(url_for('jobs.job_detail', job_id=job.id))

@bp.route('/api/jobs')
def api_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    jobs = JenkinsJob.query.order_by(JenkinsJob.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'jobs': [job.to_dict() for job in jobs.items],
        'total': jobs.total,
        'pages': jobs.pages,
        'current_page': page
    })

@bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
def api_update_job(job_id):
    job = JenkinsJob.query.get_or_404(job_id)
    data = request.get_json()
    
    allowed_fields = ['name', 'description', 'schedule', 'is_active', 'parameters']
    for field in allowed_fields:
        if field in data:
            setattr(job, field, data[field])
    
    db.session.commit()
    return jsonify(job.to_dict())