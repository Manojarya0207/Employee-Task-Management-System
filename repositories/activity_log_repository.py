from sqlalchemy.orm import Session
from models.activity_log import ActivityLog

class ActivityLogRepository:
    @staticmethod
    def create(db: Session, employee_id: str, action: str) -> ActivityLog:
        log = ActivityLog(employee_id=employee_id, action=action)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_employee_id(db: Session, employee_id: str) -> list[ActivityLog]:
        return db.query(ActivityLog).filter(ActivityLog.employee_id == employee_id).order_by(ActivityLog.timestamp.desc()).all()

    @staticmethod
    def get_all(db: Session) -> list[ActivityLog]:
        return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).all()

    @staticmethod
    def get_recent(db: Session, limit: int = 50) -> list[ActivityLog]:
        return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
