"""
services/registration_service.py

Handles the entire employee self-registration lifecycle:

  1. Employee ID generation  (MANO3210 style)
  2. Duplicate ID avoidance  (MANO3210 → MANO3210-1 → MANO3210-2 …)
  3. Creating a 'pending' registration request
  4. Admin approval / rejection
  5. Fetching requests by status
"""

import re
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.employee import Employee
from services.auth_service import hash_password, log_activity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Employee ID Generation
# ---------------------------------------------------------------------------

def generate_employee_id(name: str, phone: str) -> str:
    """
    Build a base Employee ID from name + phone.

    Rules
    -----
    - Strip spaces from name, take first 4 characters, uppercase.
    - Take first 4 digits from phone (digits only).
    - Concatenate → e.g. "Manoj Arya" + "9876543210" → "MANO9876"
    - If name has fewer than 4 letters after stripping, use all available.
    """
    # Extract letters only (ignore spaces and punctuation)
    name_letters = re.sub(r'[^a-zA-Z]', '', name).upper()
    name_part = name_letters[:4] if len(name_letters) >= 4 else name_letters

    # Extract digits only from phone, take first 4
    phone_digits = re.sub(r'\D', '', phone)
    phone_part = phone_digits[:4] if len(phone_digits) >= 4 else phone_digits

    return f"{name_part}{phone_part}"


def generate_unique_employee_id(db: Session, name: str, phone: str) -> str:
    """
    Return a guaranteed-unique Employee ID.

    Checks the database; if the base ID already exists, appends -1, -2, etc.
    """
    base_id = generate_employee_id(name, phone)
    if not base_id:
        # Fallback: timestamp-based ID
        return f"EMP{datetime.now().strftime('%H%M%S')}"

    # Check for existing IDs that start with the same base
    existing = db.query(Employee.employee_id).filter(
        Employee.employee_id.like(f"{base_id}%")
    ).all()
    existing_ids = {row[0] for row in existing}

    if base_id not in existing_ids:
        return base_id

    # Append numeric suffix until unique
    counter = 1
    while True:
        candidate = f"{base_id}-{counter}"
        if candidate not in existing_ids:
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_employee(
    db: Session,
    employee_name: str,
    phone_number: str,
    password: str,
    department: str = None,
) -> tuple[bool, str, str | None]:
    """
    Create a new 'pending' employee registration request.

    Returns
    -------
    (success, message, employee_id | None)
    """
    # --- Validation ---
    if not employee_name or len(employee_name.strip()) < 3:
        return False, "Employee name must be at least 3 characters.", None

    clean_phone = re.sub(r'\D', '', phone_number)
    if len(clean_phone) != 10:
        return False, "Phone number must be exactly 10 digits.", None

    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None

    # --- Duplicate phone check ---
    phone_exists = db.query(Employee).filter(
        Employee.phone_number == clean_phone
    ).first()
    if phone_exists:
        return False, "This phone number is already registered.", None

    # --- Generate unique ID ---
    employee_id = generate_unique_employee_id(db, employee_name.strip(), clean_phone)

    # --- Create pending record ---
    try:
        new_emp = Employee(
            employee_id=employee_id,
            employee_name=employee_name.strip(),
            phone_number=clean_phone,
            password_hash=hash_password(password),
            role='employee',
            department=department,
            joining_date=datetime.now().date(),  # placeholder until approval to satisfy DB NOT NULL constraint
            status='active',              # physical status; login gated by registration_status
            registration_status='pending',
            approved_at=None,
            rejected_at=None,
            rejection_reason=None,
        )
        db.add(new_emp)
        db.commit()
        logger.info("New registration request: %s (%s)", employee_id, employee_name)
        return True, "Registration submitted successfully. Please wait for administrator approval.", employee_id
    except Exception as exc:
        db.rollback()
        logger.error("Registration error: %s", exc)
        return False, f"Registration failed: {str(exc)}", None


# ---------------------------------------------------------------------------
# Admin: Approve / Reject
# ---------------------------------------------------------------------------

def approve_employee(db: Session, admin_id: str, employee_id: str) -> tuple[bool, str]:
    """
    Approve a pending registration request.
    Sets registration_status → 'approved' and records approval timestamp.
    """
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        return False, "Employee not found."

    if employee.registration_status == 'approved':
        return False, "Employee is already approved."

    from datetime import date
    try:
        employee.registration_status = 'approved'
        employee.approved_at = datetime.now()
        employee.joining_date = date.today()   # set joining date at approval
        employee.updated_at = datetime.now()
        db.commit()
        log_activity(db, admin_id, f"Approved registration: {employee_id}")
        logger.info("Admin '%s' approved employee '%s'.", admin_id, employee_id)
        return True, f"Employee '{employee.employee_name}' approved successfully."
    except Exception as exc:
        db.rollback()
        logger.error("Approval error: %s", exc)
        return False, f"Approval failed: {str(exc)}"


def reject_employee(
    db: Session, admin_id: str, employee_id: str, reason: str = ""
) -> tuple[bool, str]:
    """
    Reject a pending registration request.
    Sets registration_status → 'rejected' and records rejection reason + timestamp.
    """
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        return False, "Employee not found."

    if employee.registration_status == 'rejected':
        return False, "Employee is already rejected."

    try:
        employee.registration_status = 'rejected'
        employee.rejected_at = datetime.now()
        employee.rejection_reason = reason.strip() if reason else None
        employee.updated_at = datetime.now()
        db.commit()
        log_activity(db, admin_id, f"Rejected registration: {employee_id}")
        logger.info("Admin '%s' rejected employee '%s'.", admin_id, employee_id)
        return True, f"Registration for '{employee.employee_name}' has been rejected."
    except Exception as exc:
        db.rollback()
        logger.error("Rejection error: %s", exc)
        return False, f"Rejection failed: {str(exc)}"


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_pending_requests(db: Session) -> list[Employee]:
    """Return all employees with registration_status == 'pending', newest first."""
    return (
        db.query(Employee)
        .filter(Employee.registration_status == 'pending')
        .order_by(Employee.created_at.desc())
        .all()
    )


def get_all_registration_requests(
    db: Session, status_filter: str | None = None
) -> list[Employee]:
    """
    Return registration requests, optionally filtered by status.

    status_filter: 'pending' | 'approved' | 'rejected' | None (all)
    Excludes the built-in admin account seeded at startup.
    """
    query = db.query(Employee).filter(Employee.employee_id != 'admin')
    if status_filter:
        query = query.filter(Employee.registration_status == status_filter)
    return query.order_by(Employee.created_at.desc()).all()


def count_pending_requests(db: Session) -> int:
    """Return total number of pending registration requests."""
    return (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.registration_status == 'pending')
        .scalar()
        or 0
    )
