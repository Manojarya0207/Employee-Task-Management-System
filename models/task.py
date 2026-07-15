from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from models import Base

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey('employees.employee_id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='Pending') # 'Pending', 'Work In Progress', 'Completed', 'Blocked', 'On Hold'
    
    # Dates/Times generated on server
    created_date = Column(Date, nullable=False, default=func.current_date())
    created_time = Column(Time, nullable=False, default=func.current_time())
    updated_time = Column(Time, nullable=True, onupdate=func.current_time())
    last_modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    employee = relationship("Employee", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.task_id} - {self.title} ({self.status})>"
