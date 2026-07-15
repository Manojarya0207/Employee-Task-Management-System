from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from models.task import Task
from models.employee import Employee
from datetime import date

class TaskRepository:
    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Task | None:
        return db.query(Task).filter(Task.task_id == task_id).first()

    @staticmethod
    def get_by_employee_id(db: Session, employee_id: str) -> list[Task]:
        return db.query(Task).filter(Task.employee_id == employee_id).order_by(Task.created_date.desc(), Task.created_time.desc()).all()

    @staticmethod
    def create(db: Session, task: Task) -> Task:
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete(db: Session, task: Task) -> None:
        db.delete(task)
        db.commit()

    @staticmethod
    def get_filtered_tasks(
        db: Session, 
        employee_id: str = None, 
        status_filter: str = None, 
        query_str: str = None,
        start_date: date = None,
        end_date: date = None
    ) -> list[Task]:
        query = db.query(Task)
        
        if employee_id and employee_id != 'All':
            query = query.filter(Task.employee_id == employee_id)
            
        if status_filter and status_filter != 'All':
            query = query.filter(Task.status == status_filter)
            
        if start_date:
            query = query.filter(Task.created_date >= start_date)
        if end_date:
            query = query.filter(Task.created_date <= end_date)
            
        if query_str:
            search_pat = f"%{query_str}%"
            # Join with Employee to allow searching by employee name
            query = query.join(Employee, Task.employee_id == Employee.employee_id).filter(
                or_(
                    Task.title.like(search_pat),
                    Task.description.like(search_pat),
                    Employee.employee_name.like(search_pat)
                )
            )
            
        return query.order_by(Task.created_date.desc(), Task.created_time.desc()).all()

    @staticmethod
    def get_today_tasks_with_employees(db: Session, today: date) -> list[tuple[Task, Employee]]:
        return db.query(Task, Employee).join(Employee, Task.employee_id == Employee.employee_id)\
            .filter(Task.created_date == today)\
            .order_by(Task.created_time.desc()).all()

    @staticmethod
    def get_tasks_joined_with_employees(
        db: Session,
        start_date: date = None,
        end_date: date = None,
        employee_id: str = None,
        status: str = None
    ) -> list[tuple[Task, Employee]]:
        query = db.query(Task, Employee).join(Employee, Task.employee_id == Employee.employee_id)
        if start_date:
            query = query.filter(Task.created_date >= start_date)
        if end_date:
            query = query.filter(Task.created_date <= end_date)
        if employee_id and employee_id != 'All':
            query = query.filter(Task.employee_id == employee_id)
        if status and status != 'All':
            query = query.filter(Task.status == status)
        return query.order_by(Task.created_date.desc(), Task.created_time.desc()).all()

    @staticmethod
    def count_by_date(db: Session, target_date: date) -> int:
        return db.query(Task).filter(Task.created_date == target_date).count()

    @staticmethod
    def save(db: Session) -> None:
        db.commit()

