from sqlalchemy import Column, String, Date, DateTime, func
from sqlalchemy.orm import relationship
from models import Base

class Employee(Base):
    __tablename__ = 'employees'

    employee_id = Column(String(50), primary_key=True, index=True)
    employee_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='employee') # 'admin' or 'employee'
    department = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default='active') # 'active' or 'inactive'
    joining_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tasks = relationship("Task", back_populates="employee", cascade="all, delete-orphan")
    logs = relationship("ActivityLog", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.employee_id} - {self.employee_name}>"
