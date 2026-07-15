from sqlalchemy.orm import Session
from services import auth_service, registration_service

class AuthController:
    @staticmethod
    def login(db: Session, employee_id: str, password: str) -> dict:
        success, employee, message = auth_service.authenticate_user(db, employee_id, password)
        if success and employee:
            return {
                "success": True,
                "message": "Login successful",
                "data": {
                    "employee_id": employee.employee_id,
                    "employee_name": employee.employee_name,
                    "role": employee.role,
                    "status": employee.status,
                    "registration_status": employee.registration_status
                }
            }
        return {
            "success": False,
            "message": message,
            "errors": [message]
        }

    @staticmethod
    def register(db: Session, name: str, phone: str, password: str, department: str = None) -> dict:
        success, message, employee_id = registration_service.register_employee(
            db, name, phone, password, department
        )
        if success:
            return {
                "success": True,
                "message": message,
                "data": {"employee_id": employee_id}
            }
        return {
            "success": False,
            "message": message,
            "errors": [message]
        }

    @staticmethod
    def change_password(db: Session, employee_id: str, old_password: str, new_password: str) -> dict:
        success, message = auth_service.change_user_password(db, employee_id, old_password, new_password)
        if success:
            return {
                "success": True,
                "message": message,
                "data": {}
            }
        return {
            "success": False,
            "message": message,
            "errors": [message]
        }

    @staticmethod
    def get_registration_status(db: Session, employee_id: str) -> dict:
        from repositories.employee_repository import EmployeeRepository
        employee = EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            return {
                "success": False,
                "message": "Employee not found",
                "errors": ["No employee found with this ID"]
            }
        status = getattr(employee, 'registration_status', 'approved')
        reason = getattr(employee, 'rejection_reason', None)
        return {
            "success": True,
            "message": f"Registration status retrieved: {status}",
            "data": {
                "employee_id": employee.employee_id,
                "employee_name": employee.employee_name,
                "registration_status": status,
                "rejection_reason": reason
            }
        }
