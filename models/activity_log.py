from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from models import Base

class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey('employees.employee_id'), nullable=True) # Nullable for system tasks or initial setup
    action = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="logs")

    def __repr__(self):
        return f"<ActivityLog {self.log_id} - Employee: {self.employee_id} - Action: {self.action}>"
