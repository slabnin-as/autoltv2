from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import or_
from app import db
from app.models.jenkins_job_config import JenkinsJobConfig
from app.services.jenkins_service import JenkinsService

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
            JenkinsJobConfig.description.contains(search)
        ))
    
    if project:
        query = query.filter(JenkinsJobConfig.project == project)
    
    configs = query.order_by(JenkinsJobConfig.project, JenkinsJobConfig.job_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique projects for filter
    projects = db.session.query(JenkinsJobConfig.project).distinct().all()
    projects = [p[0] for p in projects]
    
    return render_template('jenkins_configs/list.html', 
                         configs=configs, projects=projects, 
                         current_project=project, search=search)

@bp.route('/api/configs')
def api_list_configs():
    """API endpoint to list Jenkins configurations"""
    project = request.args.get('project')
    jenkins_service = JenkinsService()
    
    configs = jenkins_service.get_all_configs(project=project)
    
    return jsonify({
        'configs': [config.to_dict() for config in configs],
        'total': len(configs)
    })

@bp.route('/api/projects')
def api_list_projects():
    """API endpoint to list all projects"""
    jenkins_service = JenkinsService()
    projects = jenkins_service.get_all_projects()
    
    return jsonify({'projects': projects})

@bp.route('/api/configs', methods=['POST'])
def api_create_config():
    """API endpoint to create new job configuration"""
    data = request.get_json()
    
    if not data or not all(key in data for key in ['job_name', 'job_path', 'project', 'project_url']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    config = JenkinsJobConfig(
        job_name=data['job_name'],
        job_path=data['job_path'],
        project=data['project'],
        project_url=data['project_url'],
        description=data.get('description', '')
    )
    
    try:
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'message': 'Configuration created successfully',
            'config': config.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/configs/<int:config_id>')
def api_get_config(config_id):
    """API endpoint to get specific configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    return jsonify({'config': config.to_dict()})

@bp.route('/api/configs/<int:config_id>', methods=['PUT'])
def api_update_config(config_id):
    """API endpoint to update configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update allowed fields
    for field in ['job_name', 'job_path', 'project', 'project_url', 'description']:
        if field in data:
            setattr(config, field, data[field])
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Configuration updated successfully',
            'config': config.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/configs/<int:config_id>', methods=['DELETE'])
def api_delete_config(config_id):
    """API endpoint to delete configuration"""
    config = JenkinsJobConfig.query.get_or_404(config_id)
    
    try:
        db.session.delete(config)
        db.session.commit()
        return jsonify({'message': 'Configuration deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/trigger/<int:config_id>', methods=['POST'])
def api_trigger_job(config_id):
    """API endpoint to trigger a Jenkins job"""
    data = request.get_json() or {}
    parameters = data.get('parameters', {})
    
    jenkins_service = JenkinsService()
    success, result = jenkins_service.trigger_job_by_config(config_id, parameters)
    
    if success:
        return jsonify({'success': True, 'message': result})
    else:
        return jsonify({'success': False, 'error': result}), 400

@bp.route('/api/status/<int:config_id>')
def api_get_job_status(config_id):
    """API endpoint to get job status"""
    jenkins_service = JenkinsService()
    status = jenkins_service.get_job_status(config_id)
    
    return jsonify(status)