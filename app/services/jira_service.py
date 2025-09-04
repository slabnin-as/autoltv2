from datetime import datetime, date
from jira import JIRA
from app import db
from app.models.jira_task import JiraTask
from config.config import Config

class JiraService:
    def __init__(self):
        self.jira = None
        self._connect()
    
    def _connect(self):
        try:
            self.jira = JIRA(
                server=Config.JIRA_URL,
                token_auth=Config.JIRA_API_TOKEN,
                options={'verify': False}
            )
        except Exception as e:
            print(f"Failed to connect to Jira: {e}")
            self.jira = None
    
    def search_tasks(self, jql_query, max_results=50):
        if not self.jira:
            return []
        
        try:
            issues = self.jira.search_issues(jql_query, maxResults=max_results)
            return [self._issue_to_dict(issue) for issue in issues]
        except Exception as e:
            print(f"Error searching Jira tasks: {e}")
            return []
    
    def sync_tasks_to_db(self, jql_query, max_results=50):
        if not self.jira:
            return 0
        
        synced_count = 0
        try:
            issues = self.jira.search_issues(jql_query, maxResults=max_results)
            
            for issue in issues:
                task_data = self._issue_to_dict(issue)
                existing_task = JiraTask.query.filter_by(jira_key=issue.key).first()
                
                if existing_task:
                    # Update existing task
                    for key, value in task_data.items():
                        if hasattr(existing_task, key):
                            setattr(existing_task, key, value)
                    existing_task.last_synced = datetime.now()
                else:
                    # Create new task
                    new_task = JiraTask(**task_data)
                    db.session.add(new_task)
                
                synced_count += 1
            
            db.session.commit()
            return synced_count
        except Exception as e:
            db.session.rollback()
            print(f"Error syncing tasks to database: {e}")
            return 0
    
    def sync_ekplt_autolt_tasks(self, max_results=100):
        """
        Sync tasks from EKPLT project with label 'autolt' and planned_start >= today
        """
        if not self.jira:
            return 0
        
        # Build JQL query for EKPLT project with autolt label and planned_start >= today
        today = date.today().strftime('%Y-%m-%d')
        jql_query = (
            f'project = EKPLT AND '
            f'labels = "autolt" AND '
            f'cf[10000] >= "{today}" '  # Assuming customfield_10000 is planned_start
            f'ORDER BY cf[10000] ASC'
        )
        
        print(f"JQL Query: {jql_query}")
        
        try:
            # Use expand to get all fields including custom fields
            issues = self.jira.search_issues(
                jql_query, 
                maxResults=max_results,
                expand='names'  # Get field names for debugging
            )
            
            synced_count = 0
            
            for issue in issues:
                task_data = self._issue_to_dict(issue)
                existing_task = JiraTask.query.filter_by(jira_key=issue.key).first()
                
                if existing_task:
                    # Update existing task
                    for key, value in task_data.items():
                        if hasattr(existing_task, key):
                            setattr(existing_task, key, value)
                    existing_task.last_synced = datetime.now()
                else:
                    # Create new task
                    new_task = JiraTask(**task_data)
                    db.session.add(new_task)
                
                synced_count += 1
                print(f"Synced: {issue.key} - {task_data['summary']}")
            
            db.session.commit()
            print(f"Successfully synced {synced_count} EKPLT autolt tasks")
            return synced_count
            
        except Exception as e:
            db.session.rollback()
            print(f"Error syncing EKPLT autolt tasks: {e}")
            return 0
    
    def get_jira_fields_info(self, issue_key='EKPLT-1'):
        """
        Debug method to get information about available fields in Jira
        """
        if not self.jira:
            return None
        
        try:
            issue = self.jira.issue(issue_key, expand='names')
            fields_info = {}
            
            # Get all available fields
            for field_key, field_value in issue.raw['fields'].items():
                field_name = getattr(self.jira.fields(), field_key, {}).get('name', field_key)
                fields_info[field_key] = {
                    'name': field_name,
                    'value': str(field_value)[:100] if field_value else None  # Truncate long values
                }
            
            return fields_info
        except Exception as e:
            print(f"Error getting field info: {e}")
            return None
    
    def update_task_status_and_timing(self, jira_key: str, planned_start: datetime, planned_end: datetime) -> bool:
        """
        Update JIRA task status to 'In Progress' and set planned_start/planned_end fields
        """
        if not self.jira:
            return False
        
        try:
            issue = self.jira.issue(jira_key)
            
            # Update status to 'In Progress'
            # First, get available transitions
            transitions = self.jira.transitions(issue)
            in_progress_transition = None
            
            for transition in transitions:
                if 'In Progress' in transition['name'] or 'in progress' in transition['name'].lower():
                    in_progress_transition = transition
                    break
            
            if in_progress_transition:
                self.jira.transition_issue(issue, in_progress_transition['id'])
                print(f"✅ Updated {jira_key} status to 'In Progress'")
            else:
                print(f"⚠️ No 'In Progress' transition found for {jira_key}")
            
            # Update custom fields for planned_start and planned_end
            # Note: These field IDs may need to be adjusted based on your JIRA configuration
            fields_update = {}
            
            # Assuming customfield_10000 is planned_start
            fields_update['customfield_10000'] = planned_start.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
            
            # Assuming customfield_10001 is planned_end (if exists)
            # fields_update['customfield_10001'] = planned_end.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
            
            issue.update(fields=fields_update)
            print(f"✅ Updated {jira_key} timing: Start={planned_start}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update JIRA task {jira_key}: {e}")
            return False
    
    def _issue_to_dict(self, issue):
        created_date = None
        updated_date = None
        resolved_date = None
        
        if hasattr(issue.fields, 'created') and issue.fields.created:
            created_date = datetime.strptime(issue.fields.created[:19], '%Y-%m-%dT%H:%M:%S')
        
        if hasattr(issue.fields, 'updated') and issue.fields.updated:
            updated_date = datetime.strptime(issue.fields.updated[:19], '%Y-%m-%dT%H:%M:%S')
        
        if hasattr(issue.fields, 'resolutiondate') and issue.fields.resolutiondate:
            resolved_date = datetime.strptime(issue.fields.resolutiondate[:19], '%Y-%m-%dT%H:%M:%S')
        
        # Parse planned_start field (custom field)
        planned_start = None
        if hasattr(issue.fields, 'customfield_10000') and issue.fields.customfield_10000:  # Assuming planned_start is custom field
            try:
                planned_start = datetime.strptime(issue.fields.customfield_10000[:19], '%Y-%m-%dT%H:%M:%S')
            except (ValueError, TypeError):
                planned_start = None
        
        # Parse labels
        labels = []
        if hasattr(issue.fields, 'labels') and issue.fields.labels:
            labels = list(issue.fields.labels)
        
        return {
            'jira_key': issue.key,
            'summary': issue.fields.summary,
            'description': getattr(issue.fields, 'description', ''),
            'status': issue.fields.status.name,
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
            'reporter': issue.fields.reporter.displayName if issue.fields.reporter else None,
            'priority': issue.fields.priority.name if issue.fields.priority else None,
            'issue_type': issue.fields.issuetype.name,
            'project_key': issue.fields.project.key,
            'planned_start': planned_start,
            'labels': labels,
            'created_date': created_date,
            'updated_date': updated_date,
            'resolved_date': resolved_date,
            'last_synced': datetime.now()
        }