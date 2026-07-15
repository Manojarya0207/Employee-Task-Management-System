from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.employee import Employee
from datetime import datetime

class EmployeeRepository:
    @staticmethod
    def get_by_id(db: Session, employee_id: str) -> Employee | None:
        return db.query(Employee).filter(Employee.employee_id == employee_id).first()

    @staticmethod
    def get_by_phone(db: Session, phone_number: str) -> Employee | None:
        return db.query(Employee).filter(Employee.phone_number == phone_number).first()

    @staticmethod
    def get_all(db: Session) -> list[Employee]:
        return db.query(Employee).filter(Employee.registration_status == 'approved').order_by(Employee.employee_id).all()

    @staticmethod
    def search(db: Session, query_str: str) -> list[Employee]:
        search_pattern = f"%{query_str}%"
        return db.query(Employee).filter(
            Employee.registration_status == 'approved',
            or_(
                Employee.employee_id.like(search_pattern),
                Employee.employee_name.like(search_pattern),
                Employee.phone_number.like(search_pattern),
                Employee.department.like(search_pattern)
            )
        ).order_by(Employee.employee_id).all()

    @staticmethod
    def get_by_registration_status(db: Session, status: str) -> list[Employee]:
        return db.query(Employee).filter(Employee.registration_status == status).order_by(Employee.created_at.desc()).all()

    @staticmethod
    def create(db: Session, employee: Employee) -> Employee:
        db.add(employee)
        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def count_all(db: Session) -> int:
        return db.query(Employee).count()

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        return db.query(Employee).filter(Employee.status == status).count()

    @staticmethod
    def count_by_role(db: Session, role: str) -> int:
        return db.query(Employee).filter(Employee.role == role).count()

    @staticmethod
    def save(db: Session) -> None:
        db.commit()

