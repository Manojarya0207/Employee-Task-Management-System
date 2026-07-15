from sqlalchemy.orm import Session
from sqlalchemy import func
from models.task import Task
from models.employee import Employee
from models.activity_log import ActivityLog
from datetime import date

class DashboardController:
    @staticmethod
    def get_admin_metrics(db: Session) -> dict:
        today = date.today()
        
        # Calculate employee metrics
        total_employees = db.query(func.count(Employee.employee_id)).filter(Employee.registration_status == 'approved').scalar() or 0
        active_employees = db.query(func.count(Employee.employee_id)).filter(Employee.registration_status == 'approved', Employee.status == 'active').scalar() or 0
        
        # Calculate task metrics for today
        today_tasks = db.query(Task).filter(Task.created_date == today).all()
        total_tasks_today = len(today_tasks)
        completed_today = sum(1 for t in today_tasks if t.status == 'Completed')
        wip_today = sum(1 for t in today_tasks if t.status == 'Work In Progress')
        blocked_today = sum(1 for t in today_tasks if t.status == 'Blocked')
        on_hold_today = sum(1 for t in today_tasks if t.status == 'On Hold')
        pending_today = total_tasks_today - completed_today - wip_today - blocked_today - on_hold_today
        
        # Recent activity logs
        recent_logs = db.query(ActivityLog, Employee).join(Employee, ActivityLog.employee_id == Employee.employee_id)\
            .order_by(ActivityLog.timestamp.desc()).limit(10).all()

        return {
            "success": True,
            "message": "Admin metrics retrieved",
            "data": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "today_stats": {
                    "total": total_tasks_today,
                    "completed": completed_today,
                    "wip": wip_today,
                    "blocked": blocked_today,
                    "on_hold": on_hold_today,
                    "pending": pending_today
                },
                "recent_activities": [
                    {
                        "log_id": log.log_id,
                        "employee_name": emp.employee_name,
                        "action": log.action,
                        "time": log.timestamp.strftime('%I:%M %p')
                    }
                    for log, emp in recent_logs
                ]
            }
        }

    @staticmethod
    def get_employee_metrics(db: Session, employee_id: str) -> dict:
        # Calculate counts
        all_tasks = db.query(Task).filter(Task.employee_id == employee_id).all()
        total = len(all_tasks)
        completed = sum(1 for t in all_tasks if t.status == 'Completed')
        wip = sum(1 for t in all_tasks if t.status == 'Work In Progress')
        blocked = sum(1 for t in all_tasks if t.status == 'Blocked')
        on_hold = sum(1 for t in all_tasks if t.status == 'On Hold')
        pending = total - completed - wip - blocked - on_hold

        return {
            "success": True,
            "message": "Employee metrics retrieved",
            "data": {
                "total": total,
                "completed": completed,
                "wip": wip,
                "blocked": blocked,
                "on_hold": on_hold,
                "pending": pending
            }
        }
