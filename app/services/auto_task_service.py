from datetime import datetime
from app.services.jira_service import JiraService
from app.services.task_scheduler_service import TaskSchedulerService

class AutoTaskService:
    """Service for automated task synchronization and scheduling"""
    
    def __init__(self):
        self.jira_service = JiraService()
        self.scheduler_service = TaskSchedulerService()
    
    def sync_and_schedule_tasks(self) -> dict:
        """
        Main automation method:
        1. Sync EKPLT tasks from JIRA
        2. Schedule open tasks automatically
        """
        print(f"🤖 Starting automated task sync and scheduling at {datetime.now()}")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'sync_result': {},
            'schedule_result': {},
            'success': False
        }
        
        try:
            # Step 1: Sync EKPLT tasks
            print("📥 Syncing EKPLT tasks from JIRA...")
            synced_count = self.jira_service.sync_ekplt_autolt_tasks(max_results=100)
            result['sync_result'] = {
                'synced_count': synced_count,
                'success': synced_count >= 0
            }
            
            if synced_count > 0:
                print(f"✅ Synced {synced_count} tasks from JIRA")
            else:
                print("ℹ️ No new tasks to sync")
            
            # Step 2: Schedule open tasks
            print("📅 Scheduling open tasks...")
            schedule_result = self.scheduler_service.schedule_next_tasks()
            result['schedule_result'] = schedule_result
            
            if schedule_result['scheduled'] > 0:
                print(f"✅ Scheduled {schedule_result['scheduled']} tasks")
            else:
                print("ℹ️ No tasks to schedule")
            
            result['success'] = True
            result['message'] = f"Synced {synced_count} tasks, scheduled {schedule_result['scheduled']} tasks"
            
        except Exception as e:
            print(f"❌ Error in automated task processing: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        print(f"🏁 Automation completed: {result['message'] if result['success'] else result.get('error', 'Unknown error')}")
        return result
    
    def sync_tasks_only(self) -> dict:
        """Sync tasks only without scheduling"""
        try:
            synced_count = self.jira_service.sync_ekplt_autolt_tasks(max_results=100)
            return {
                'timestamp': datetime.now().isoformat(),
                'synced_count': synced_count,
                'success': True,
                'message': f"Synced {synced_count} tasks"
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def schedule_tasks_only(self) -> dict:
        """Schedule tasks only without syncing"""
        try:
            result = self.scheduler_service.schedule_next_tasks()
            result['timestamp'] = datetime.now().isoformat()
            return result
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }