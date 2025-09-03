from datetime import datetime
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
                basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
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
                    existing_task.last_synced = datetime.utcnow()
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
            'created_date': created_date,
            'updated_date': updated_date,
            'resolved_date': resolved_date,
            'last_synced': datetime.utcnow()
        }