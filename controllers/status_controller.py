from sqlalchemy.orm import Session
from models.status import TaskStatus, EmployeeStatus
from repositories.status_repository import StatusRepository

class StatusController:
    @staticmethod
    def get_task_statuses(db: Session) -> dict:
        statuses = StatusRepository.get_all_task_statuses(db)
        return {
            "success": True,
            "message": "Task statuses retrieved",
            "data": [
                {
                    "name": s.name,
                    "description": s.description,
                    "color": s.color
                }
                for s in statuses
            ]
        }

    @staticmethod
    def get_employee_statuses(db: Session) -> dict:
        statuses = StatusRepository.get_all_employee_statuses(db)
        return {
            "success": True,
            "message": "Employee statuses retrieved",
            "data": [
                {
                    "name": s.name,
                    "description": s.description,
                    "color": s.color
                }
                for s in statuses
            ]
        }

    @staticmethod
    def add_task_status(db: Session, name: str, description: str, color: str) -> dict:
        existing = StatusRepository.get_task_status_by_name(db, name)
        if existing:
            return {"success": False, "message": f"Task status '{name}' already exists", "errors": ["Status already exists"]}
        
        status = TaskStatus(name=name, description=description, color=color)
        StatusRepository.create_task_status(db, status)
        return {"success": True, "message": "Task status created successfully", "data": {}}

    @staticmethod
    def add_employee_status(db: Session, name: str, description: str, color: str) -> dict:
        existing = StatusRepository.get_employee_status_by_name(db, name)
        if existing:
            return {"success": False, "message": f"Employee status '{name}' already exists", "errors": ["Status already exists"]}
        
        status = EmployeeStatus(name=name, description=description, color=color)
        StatusRepository.create_employee_status(db, status)
        return {"success": True, "message": "Employee status created successfully", "data": {}}

    @staticmethod
    def delete_task_status(db: Session, name: str) -> dict:
        status = StatusRepository.get_task_status_by_name(db, name)
        if not status:
            return {"success": False, "message": "Status not found", "errors": ["Status not found"]}
        StatusRepository.delete_task_status(db, status)
        return {"success": True, "message": "Task status deleted successfully", "data": {}}

    @staticmethod
    def delete_employee_status(db: Session, name: str) -> dict:
        status = StatusRepository.get_employee_status_by_name(db, name)
        if not status:
            return {"success": False, "message": "Status not found", "errors": ["Status not found"]}
        StatusRepository.delete_employee_status(db, status)
        return {"success": True, "message": "Employee status deleted successfully", "data": {}}
