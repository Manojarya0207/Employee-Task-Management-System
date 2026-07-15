from sqlalchemy.orm import Session
from services import task_service
from repositories.task_repository import TaskRepository
from datetime import date

class TaskController:
    @staticmethod
    def get_by_id(db: Session, task_id: int) -> dict:
        task = task_service.get_task_by_id(db, task_id)
        if task:
            return {
                "success": True,
                "message": "Task retrieved",
                "data": {
                    "task_id": task.task_id,
                    "employee_id": task.employee_id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_date": str(task.created_date),
                    "created_time": str(task.created_time)
                }
            }
        return {"success": False, "message": "Task not found", "errors": ["Task not found"]}

    @staticmethod
    def get_employee_tasks(db: Session, employee_id: str) -> dict:
        tasks = task_service.get_employee_tasks(db, employee_id)
        return {
            "success": True,
            "message": "Employee tasks retrieved",
            "data": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "created_date": str(t.created_date),
                    "created_time": str(t.created_time)
                }
                for t in tasks
            ]
        }

    @staticmethod
    def add(db: Session, employee_id: str, title: str, description: str, status: str) -> dict:
        success, message = task_service.add_task(db, employee_id, title, description, status)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def update(db: Session, employee_id: str, task_id: int, title: str, description: str, status: str) -> dict:
        success, message = task_service.update_task(db, employee_id, task_id, title, description, status)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def get_filtered(db: Session, employee_id: str = None, status: str = None, query_str: str = None, start_date = None, end_date = None) -> dict:
        tasks = task_service.get_filtered_tasks(db, employee_id, status, query_str, start_date, end_date)
        return {
            "success": True,
            "message": "Filtered tasks retrieved",
            "data": [
                {
                    "task_id": t.task_id,
                    "employee_id": t.employee_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "created_date": str(t.created_date),
                    "created_time": str(t.created_time)
                }
                for t in tasks
            ]
        }

    @staticmethod
    def get_by_period(db: Session, employee_id: str, period: str) -> dict:
        tasks = task_service.get_tasks_by_period(db, employee_id, period)
        return {
            "success": True,
            "message": f"Tasks for period {period} retrieved",
            "data": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "created_date": str(t.created_date),
                    "created_time": str(t.created_time)
                }
                for t in tasks
            ]
        }

    @staticmethod
    def get_calendar_events(db: Session, employee_id: str) -> dict:
        events = task_service.get_calendar_events(db, employee_id)
        return {
            "success": True,
            "message": "Calendar events formatted",
            "data": events
        }

    @staticmethod
    def get_daily_tasks_data(db: Session) -> dict:
        today = date.today()
        tasks = TaskRepository.get_today_tasks_with_employees(db, today)
        return {
            "success": True,
            "message": "Today's task summary retrieved",
            "data": [
                {
                    "task_id": t.task_id,
                    "time": t.created_time.strftime('%I:%M %p'),
                    "employee_id": e.employee_id,
                    "employee_name": e.employee_name,
                    "department": e.department or 'N/A',
                    "title": t.title,
                    "description": t.description or 'No description.',
                    "status": t.status
                }
                for t, e in tasks
            ]
        }
