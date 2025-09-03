from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import or_
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.services.multi_jenkins_service import MultiJenkinsService

bp = Blueprint('jenkins_configs', __name__)

@bp.route('/')
def list_configs():
    """List all Jenkins job configurations"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    project = request.args.get('project', '')
    
    query = JenkinsJobConfig.query
    
    if search:
        query = query.filter(or_(
            JenkinsJobConfig.job_name.contains(search),
            JenkinsJobConfig.display_name.contains(search),
            JenkinsJobConfig.description.contains(search)
        ))
    
    if project:
        query = query.filter(JenkinsJobConfig.project_name == project)
    
    configs = query.order_by(JenkinsJobConfig.project_name, JenkinsJobConfig.job_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique projects for filter
    projects = db.session.query(JenkinsJobConfig.project_name).distinct().all()
    projects = [p[0] for p in projects]
    
    return render_template('jenkins_configs/list.html',
                         configs=configs,
                         search=search,
                         current_project=project,
                         projects=projects)

@bp.route('/<int:config_id>')
def config_detail(config_id):
    """Show detailed information about a Jenkins job configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    
    # Get job status
    jenkins_service = MultiJenkinsService()
    status_info = jenkins_service.get_job_status(config_id)
    
    return render_template('jenkins_configs/detail.html',
                         config=config,
                         status_info=status_info)

@bp.route('/trigger/<int:config_id>', methods=['POST'])
def trigger_job(config_id):
    """Trigger a Jenkins job"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    
    # Get parameters from form
    parameters = {}
    for key, value in request.form.items():
        if key.startswith('param_'):
            param_name = key[6:]  # Remove 'param_' prefix
            parameters[param_name] = value
    
    triggered_by = request.form.get('triggered_by', 'Web Interface')
    
    jenkins_service = MultiJenkinsService()
    success, result = jenkins_service.trigger_job_by_config(config_id, parameters, triggered_by)
    
    if success:
        flash(f'Job {config.job_name} triggered successfully!', 'success')
        if isinstance(result, dict) and 'build_number' in result:
            flash(f'Build number: {result["build_number"]}', 'info')
    else:
        flash(f'Failed to trigger job: {result}', 'error')
    
    return redirect(url_for('jenkins_configs.config_detail', config_id=config_id))

@bp.route('/trigger-project/<project_name>', methods=['POST'])
def trigger_project_jobs(project_name):
    """Trigger all jobs in a project"""
    triggered_by = request.form.get('triggered_by', 'Web Interface')
    
    jenkins_service = MultiJenkinsService()
    success, result = jenkins_service.bulk_trigger_by_project(project_name, triggered_by=triggered_by)
    
    if success:
        flash(result['message'], 'success')
    else:
        flash(f'Failed to trigger project jobs: {result}', 'error')
    
    return redirect(url_for('jenkins_configs.list_configs', project=project_name))

# API Endpoints

@bp.route('/api/configs')
def api_list_configs():
    """API endpoint to list job configurations"""
    project = request.args.get('project')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = JenkinsJobConfig.query
    if project:
        query = query.filter_by(project_name=project)
    if active_only:
        query = query.filter_by(is_active=True)
    
    configs = query.order_by(JenkinsJobConfig.project_name, JenkinsJobConfig.job_name).all()
    
    return jsonify({
        'configs': [config.to_dict_safe() for config in configs],
        'total': len(configs)
    })

@bp.route('/api/projects')
def api_list_projects():
    """API endpoint to list all projects"""
    jenkins_service = MultiJenkinsService()
    projects = jenkins_service.get_all_projects()
    
    return jsonify({'projects': projects})

@bp.route('/api/configs', methods=['POST'])
def api_create_config():
    """API endpoint to create new job configuration"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['job_name', 'project_name', 'jenkins_url', 'job_path']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if config already exists
    existing = JenkinsJobConfig.query.filter_by(
        job_name=data['job_name'],
        project_name=data['project_name']
    ).first()
    
    if existing:
        return jsonify({'error': 'Job configuration already exists for this project'}), 409
    
    try:
        config = JenkinsJobConfig(
            job_name=data['job_name'],
            display_name=data.get('display_name'),
            project_name=data['project_name'],
            jenkins_url=data['jenkins_url'],
            job_path=data['job_path'],
            description=data.get('description'),
            parameters=data.get('parameters', {}),
            environment=data.get('environment', 'production'),
            is_active=data.get('is_active', True),
            is_manual_only=data.get('is_manual_only', False),
            max_concurrent_builds=data.get('max_concurrent_builds', 1),
            username=data.get('username'),
            api_token=data.get('api_token'),
            created_by=data.get('created_by', 'API')
        )
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'message': 'Job configuration created successfully',
            'config': config.to_dict_safe()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create configuration: {str(e)}'}), 500

@bp.route('/api/configs/<int:config_id>', methods=['PUT'])
def api_update_config(config_id):
    """API endpoint to update job configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    data = request.get_json()
    
    try:
        # Update allowed fields
        allowed_fields = [
            'display_name', 'description', 'parameters', 'environment',
            'is_active', 'is_manual_only', 'max_concurrent_builds',
            'jenkins_url', 'job_path', 'username', 'api_token'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(config, field, data[field])
        
        config.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Configuration updated successfully',
            'config': config.to_dict_safe()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update configuration: {str(e)}'}), 500

@bp.route('/api/trigger/<int:config_id>', methods=['POST'])
def api_trigger_job(config_id):
    """API endpoint to trigger a Jenkins job"""
    data = request.get_json() or {}
    
    parameters = data.get('parameters', {})
    triggered_by = data.get('triggered_by', 'API')
    
    jenkins_service = MultiJenkinsService()
    success, result = jenkins_service.trigger_job_by_config(config_id, parameters, triggered_by)
    
    if success:
        return jsonify({
            'success': True,
            'result': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400

@bp.route('/api/trigger-project/<project_name>', methods=['POST'])
def api_trigger_project(project_name):
    """API endpoint to trigger all jobs in a project"""
    data = request.get_json() or {}
    
    parameters = data.get('parameters', {})
    triggered_by = data.get('triggered_by', 'API')
    
    jenkins_service = MultiJenkinsService()
    success, result = jenkins_service.bulk_trigger_by_project(
        project_name, 
        parameters, 
        triggered_by
    )
    
    if success:
        return jsonify({
            'success': True,
            'result': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400

@bp.route('/api/status/<int:config_id>')
def api_get_job_status(config_id):
    """API endpoint to get job status"""
    jenkins_service = MultiJenkinsService()
    status_info = jenkins_service.get_job_status(config_id)
    
    if status_info:
        return jsonify(status_info)
    else:
        return jsonify({'error': 'Could not retrieve job status'}), 404

@bp.route('/api/validate/<int:config_id>')
def api_validate_config(config_id):
    """API endpoint to validate job configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    
    jenkins_service = MultiJenkinsService()
    is_valid, message = jenkins_service.validate_job_config(config)
    
    return jsonify({
        'valid': is_valid,
        'message': message,
        'config_id': config_id
    })