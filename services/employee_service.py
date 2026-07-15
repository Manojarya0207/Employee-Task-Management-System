from sqlalchemy.orm import Session
from models.employee import Employee
from services.auth_service import hash_password, log_activity
from datetime import datetime, date
from repositories.employee_repository import EmployeeRepository

def get_employee_by_id(db: Session, employee_id: str) -> Employee | None:
    """Retrieves an employee by their unique ID."""
    return EmployeeRepository.get_by_id(db, employee_id)

def get_all_employees(db: Session) -> list[Employee]:
    """Retrieves all employees in the system."""
    return EmployeeRepository.get_all(db)

def search_employees(db: Session, query_str: str) -> list[Employee]:
    """Searches employees by ID, Name, Phone, or Department."""
    if not query_str:
        return get_all_employees(db)
    return EmployeeRepository.search(db, query_str)

def add_employee(
    db: Session, 
    creator_id: str,
    employee_id: str, 
    employee_name: str, 
    phone_number: str, 
    password: str, 
    role: str = 'employee', 
    department: str = None, 
    joining_date: date = None
) -> tuple[bool, str]:
    """
    Creates a new employee account.
    Validates Employee ID uniqueness.
    """
    if not employee_id or not employee_name or not phone_number or not password:
        return False, "All required fields (ID, Name, Phone, Password) must be filled"
        
    existing = EmployeeRepository.get_by_id(db, employee_id)
    if existing:
        return False, f"Employee ID '{employee_id}' already exists"
        
    if not joining_date:
        joining_date = date.today()
        
    try:
        new_emp = Employee(
            employee_id=employee_id.strip(),
            employee_name=employee_name.strip(),
            phone_number=phone_number.strip(),
            password_hash=hash_password(password),
            role=role,
            department=department.strip() if department else None,
            joining_date=joining_date,
            status='active',
            registration_status='approved'  # Added by default for admin actions
        )
        EmployeeRepository.create(db, new_emp)
        log_activity(db, creator_id, f"Added employee: {employee_id}")
        return True, "Employee added successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def update_employee(
    db: Session, 
    updater_id: str,
    employee_id: str, 
    employee_name: str, 
    phone_number: str, 
    department: str, 
    status: str
) -> tuple[bool, str]:
    """
    Updates an existing employee's details.
    Employee ID is immutable.
    """
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if not employee_name or not phone_number or not status:
        return False, "Name, Phone, and Status are required fields"
        
    try:
        employee.employee_name = employee_name.strip()
        employee.phone_number = phone_number.strip()
        employee.department = department.strip() if department else None
        employee.status = status
        employee.updated_at = datetime.now()
        
        EmployeeRepository.save(db)
        log_activity(db, updater_id, f"Updated employee details: {employee_id}")
        return True, "Employee updated successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def toggle_employee_status(db: Session, updater_id: str, employee_id: str) -> tuple[bool, str]:
    """Toggles employee account status between active and inactive."""
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if employee_id == updater_id:
        return False, "You cannot disable your own account!"
        
    new_status = 'inactive' if employee.status == 'active' else 'active'
    try:
        employee.status = new_status
        employee.updated_at = datetime.now()
        EmployeeRepository.save(db)
        
        log_activity(db, updater_id, f"Toggled employee status to {new_status}: {employee_id}")
        return True, f"Employee is now {new_status}"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def delete_employee(db: Session, admin_id: str, employee_id: str) -> tuple[bool, str]:
    """Deletes an employee account and its related tasks/activity logs."""
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"

    if employee_id == admin_id:
        return False, "You cannot delete your own account!"

    if employee.role == 'admin':
        # Quick check for other admin accounts
        all_emps = EmployeeRepository.get_all(db)
        admin_count = sum(1 for e in all_emps if e.role == 'admin')
        if admin_count <= 1:
            return False, "You cannot delete the last administrator account"

    try:
        db.delete(employee)
        db.commit()

        log_activity(db, admin_id, f"Deleted employee: {employee_id}")
        return True, "Employee deleted successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def reset_employee_password(db: Session, admin_id: str, employee_id: str, new_password: str) -> tuple[bool, str]:
    """Allows an administrator to reset an employee's password."""
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters long"
        
    try:
        employee.password_hash = hash_password(new_password)
        employee.updated_at = datetime.now()
        EmployeeRepository.save(db)
        
        log_activity(db, admin_id, f"Reset password for employee: {employee_id}")
        return True, "Password reset successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
