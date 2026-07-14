from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.employee import Employee
from services.auth_service import hash_password, log_activity
from datetime import datetime, date

def get_employee_by_id(db: Session, employee_id: str) -> Employee | None:
    """Retrieves an employee by their unique ID."""
    return db.query(Employee).filter(Employee.employee_id == employee_id).first()

def get_all_employees(db: Session) -> list[Employee]:
    """Retrieves all employees in the system."""
    return db.query(Employee).order_by(Employee.employee_id).all()

def search_employees(db: Session, query_str: str) -> list[Employee]:
    """Searches employees by ID, Name, Phone, or Department."""
    if not query_str:
        return get_all_employees(db)
        
    search_pattern = f"%{query_str}%"
    return db.query(Employee).filter(
        or_(
            Employee.employee_id.like(search_pattern),
            Employee.employee_name.like(search_pattern),
            Employee.phone_number.like(search_pattern),
            Employee.department.like(search_pattern)
        )
    ).order_by(Employee.employee_id).all()

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
    # Validation checks
    if not employee_id or not employee_name or not phone_number or not password:
        return False, "All required fields (ID, Name, Phone, Password) must be filled"
        
    existing = get_employee_by_id(db, employee_id)
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
            status='active'
        )
        db.add(new_emp)
        db.commit()
        
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
    employee = get_employee_by_id(db, employee_id)
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
        
        db.commit()
        log_activity(db, updater_id, f"Updated employee details: {employee_id}")
        return True, "Employee updated successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def toggle_employee_status(db: Session, updater_id: str, employee_id: str) -> tuple[bool, str]:
    """Toggles employee account status between active and inactive."""
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if employee_id == updater_id:
        return False, "You cannot disable your own account!"
        
    new_status = 'inactive' if employee.status == 'active' else 'active'
    try:
        employee.status = new_status
        employee.updated_at = datetime.now()
        db.commit()
        
        log_activity(db, updater_id, f"Toggled employee status to {new_status}: {employee_id}")
        return True, f"Employee is now {new_status}"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def delete_employee(db: Session, admin_id: str, employee_id: str) -> tuple[bool, str]:
    """Deletes an employee account and its related tasks/activity logs."""
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"

    if employee_id == admin_id:
        return False, "You cannot delete your own account!"

    if employee.role == 'admin':
        admin_count = db.query(Employee).filter(Employee.role == 'admin').count()
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
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        return False, "Employee not found"
        
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters long"
        
    try:
        employee.password_hash = hash_password(new_password)
        employee.updated_at = datetime.now()
        db.commit()
        
        log_activity(db, admin_id, f"Reset password for employee: {employee_id}")
        return True, "Password reset successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
