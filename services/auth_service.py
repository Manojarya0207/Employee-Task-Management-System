from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from models.employee import Employee
from datetime import datetime
from repositories.employee_repository import EmployeeRepository
from repositories.activity_log_repository import ActivityLogRepository

def hash_password(password: str) -> str:
    """Generates a secure password hash."""
    return generate_password_hash(password, method='scrypt')

def check_password(password_hash: str, password: str) -> bool:
    """Checks if a password matches its hash."""
    return check_password_hash(password_hash, password)

def log_activity(db: Session, employee_id: str, action: str):
    """Inserts a new audit log record."""
    try:
        ActivityLogRepository.create(db, employee_id, action)
    except Exception as e:
        print(f"Error logging activity: {e}")

def authenticate_user(db: Session, employee_id: str, password: str) -> tuple[bool, Employee | None, str]:
    """
    Validates employee_id and password.

    Login is blocked until registration_status == 'approved'.
    Returns (success, Employee_object or None, error_message).
    """
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, None, "Invalid Employee ID or Password."

    # --- Registration approval gate ---
    reg_status = getattr(employee, 'registration_status', 'approved')  # safe default for legacy rows
    if reg_status == 'pending':
        return False, None, "Your account is waiting for administrator approval."
    if reg_status == 'rejected':
        reason = getattr(employee, 'rejection_reason', None)
        base_msg = "Your registration request has been rejected. Please contact the administrator."
        return False, None, f"{base_msg}\nReason: {reason}" if reason else base_msg

    # --- Account active check ---
    if employee.status != 'active':
        return False, None, "Your account has been disabled. Please contact the administrator."

    # --- Password verification ---
    if not check_password(employee.password_hash, password):
        return False, None, "Invalid Employee ID or Password."

    # Log successful login
    log_activity(db, employee_id, "User logged in")
    return True, employee, "Success"


def change_user_password(db: Session, employee_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Allows user to update their own password.
    Verifies old password before applying the new one.
    """
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if not check_password(employee.password_hash, old_password):
        return False, "Current password does not match"
        
    # Validate password strength (simple check)
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long"
        
    employee.password_hash = hash_password(new_password)
    employee.updated_at = datetime.now()
    
    try:
        EmployeeRepository.save(db)
        log_activity(db, employee_id, "Password changed by user")
        return True, "Password changed successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
