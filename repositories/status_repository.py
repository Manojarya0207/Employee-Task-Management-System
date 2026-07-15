from sqlalchemy.orm import Session
from models.status import TaskStatus, EmployeeStatus

class StatusRepository:
    @staticmethod
    def get_all_task_statuses(db: Session) -> list[TaskStatus]:
        return db.query(TaskStatus).all()

    @staticmethod
    def get_all_employee_statuses(db: Session) -> list[EmployeeStatus]:
        return db.query(EmployeeStatus).all()

    @staticmethod
    def get_task_status_by_name(db: Session, name: str) -> TaskStatus | None:
        return db.query(TaskStatus).filter(TaskStatus.name == name).first()

    @staticmethod
    def get_employee_status_by_name(db: Session, name: str) -> EmployeeStatus | None:
        return db.query(EmployeeStatus).filter(EmployeeStatus.name == name).first()

    @staticmethod
    def create_task_status(db: Session, status: TaskStatus) -> TaskStatus:
        db.add(status)
        db.commit()
        db.refresh(status)
        return status

    @staticmethod
    def create_employee_status(db: Session, status: EmployeeStatus) -> EmployeeStatus:
        db.add(status)
        db.commit()
        db.refresh(status)
        return status

    @staticmethod
    def delete_task_status(db: Session, status: TaskStatus) -> None:
        db.delete(status)
        db.commit()

    @staticmethod
    def delete_employee_status(db: Session, status: EmployeeStatus) -> None:
        db.delete(status)
        db.commit()

    @staticmethod
    def save(db: Session) -> None:
        db.commit()
