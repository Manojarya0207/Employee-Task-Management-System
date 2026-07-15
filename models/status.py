from sqlalchemy import Column, Integer, String
from models import Base

class TaskStatus(Base):
    __tablename__ = 'task_statuses'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    color = Column(String(7), nullable=False, default='#6b7280')

class EmployeeStatus(Base):
    __tablename__ = 'employee_statuses'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    color = Column(String(7), nullable=False, default='#6b7280')
