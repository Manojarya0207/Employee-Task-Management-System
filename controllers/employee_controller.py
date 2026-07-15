from sqlalchemy.orm import Session
from services import employee_service, registration_service

class EmployeeController:
    @staticmethod
    def get_all(db: Session) -> dict:
        employees = employee_service.get_all_employees(db)
        return {
            "success": True,
            "message": "Employees retrieved successfully",
            "data": [
                {
                    "employee_id": e.employee_id,
                    "employee_name": e.employee_name,
                    "phone_number": e.phone_number,
                    "role": e.role,
                    "department": e.department,
                    "status": e.status,
                    "joining_date": str(e.joining_date) if e.joining_date else None,
                    "registration_status": e.registration_status
                }
                for e in employees
            ]
        }

    @staticmethod
    def search(db: Session, query_str: str) -> dict:
        employees = employee_service.search_employees(db, query_str)
        return {
            "success": True,
            "message": f"Search results for query: {query_str}",
            "data": [
                {
                    "employee_id": e.employee_id,
                    "employee_name": e.employee_name,
                    "phone_number": e.phone_number,
                    "role": e.role,
                    "department": e.department,
                    "status": e.status,
                    "joining_date": str(e.joining_date) if e.joining_date else None
                }
                for e in employees
            ]
        }

    @staticmethod
    def add(db: Session, creator_id: str, employee_id: str, name: str, phone: str, password: str, role: str = 'employee', department: str = None, joining_date = None) -> dict:
        success, message = employee_service.add_employee(
            db, creator_id, employee_id, name, phone, password, role, department, joining_date
        )
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def update(db: Session, updater_id: str, employee_id: str, name: str, phone: str, department: str, status: str) -> dict:
        success, message = employee_service.update_employee(
            db, updater_id, employee_id, name, phone, department, status
        )
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def delete(db: Session, admin_id: str, employee_id: str) -> dict:
        success, message = employee_service.delete_employee(db, admin_id, employee_id)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def reset_password(db: Session, admin_id: str, employee_id: str, new_password: str) -> dict:
        success, message = employee_service.reset_employee_password(db, admin_id, employee_id, new_password)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def toggle_status(db: Session, updater_id: str, employee_id: str) -> dict:
        success, message = employee_service.toggle_employee_status(db, updater_id, employee_id)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def get_pending_registrations(db: Session) -> dict:
        requests = registration_service.get_pending_requests(db)
        return {
            "success": True,
            "message": "Pending registration requests retrieved",
            "data": [
                {
                    "employee_id": r.employee_id,
                    "employee_name": r.employee_name,
                    "phone_number": r.phone_number,
                    "department": r.department,
                    "created_at": str(r.created_at)
                }
                for r in requests
            ]
        }

    @staticmethod
    def approve_registration(db: Session, admin_id: str, employee_id: str) -> dict:
        success, message = registration_service.approve_employee(db, admin_id, employee_id)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}

    @staticmethod
    def reject_registration(db: Session, admin_id: str, employee_id: str, reason: str = "") -> dict:
        success, message = registration_service.reject_employee(db, admin_id, employee_id, reason)
        if success:
            return {"success": True, "message": message, "data": {}}
        return {"success": False, "message": message, "errors": [message]}
