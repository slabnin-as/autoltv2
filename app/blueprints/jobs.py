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
    jobs = JenkinsJobConfig.query.order_by(JenkinsJobConfig.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('jobs/list.html', jobs=jobs)

@bp.route('/<int:job_id>')
def job_detail(job_id):
    job = JenkinsJobConfig.query.get_or_404(job_id)
    return render_template('jobs/detail.html', job=job)

@bp.route('/create', methods=['GET', 'POST'])
def create_job():
    if request.method == 'POST':
        job = JenkinsJobConfig(
            job_name=request.form['job_name'],
            job_path=request.form['job_path'],
            project=request.form['project'],
            project_url=request.form['project_url'],
            description=request.form.get('description', '')
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job configuration successfully created', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('jobs/create.html')

@bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    job = JenkinsJobConfig.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.job_name = request.form['job_name']
        job.job_path = request.form['job_path']
        job.project = request.form['project']
        job.project_url = request.form['project_url']
        job.description = request.form.get('description', '')
        
        db.session.commit()
        flash('Job configuration successfully updated', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('jobs/edit.html', job=job)

@bp.route('/<int:job_id>/trigger', methods=['POST'])
def trigger_job(job_id):
    job = JenkinsJobConfig.query.get_or_404(job_id)
    jenkins_service = JenkinsService()
    
    success, message = jenkins_service.trigger_job_by_config(job_id)
    
    if success:
        flash(f'Job {job.job_name} successfully triggered', 'success')
    else:
        flash(f'Failed to trigger job: {message}', 'error')
    
    return redirect(url_for('jobs.job_detail', job_id=job.id))

@bp.route('/api/jobs')
def api_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    jobs = JenkinsJobConfig.query.order_by(JenkinsJobConfig.id.desc()).paginate(
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
    job = JenkinsJobConfig.query.get_or_404(job_id)
    data = request.get_json()
    
    allowed_fields = ['job_name', 'job_path', 'project', 'project_url', 'description']
    for field in allowed_fields:
        if field in data:
            setattr(job, field, data[field])
    
    db.session.commit()
    return jsonify(job.to_dict())