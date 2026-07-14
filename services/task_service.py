from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from models.task import Task
from models.employee import Employee
from services.auth_service import log_activity
from datetime import date, datetime, timedelta

def get_task_by_id(db: Session, task_id: int) -> Task | None:
    """Retrieves a task by its unique numeric ID."""
    return db.query(Task).filter(Task.task_id == task_id).first()

def get_employee_tasks(db: Session, employee_id: str) -> list[Task]:
    """Retrieves all tasks associated with a specific employee."""
    return db.query(Task).filter(Task.employee_id == employee_id).order_by(Task.created_date.desc(), Task.created_time.desc()).all()

def add_task(
    db: Session, 
    employee_id: str, 
    title: str, 
    description: str, 
    status: str
) -> tuple[bool, str]:
    """
    Submits a task for today.
    The date and time are generated on the server.
    """
    if not title:
        return False, "Task title is required"
        
    try:
        new_task = Task(
            employee_id=employee_id,
            title=title.strip(),
            description=description.strip() if description else None,
            status=status,
            created_date=date.today(),
            created_time=datetime.now().time()
        )
        db.add(new_task)
        db.commit()
        
        log_activity(db, employee_id, f"Created task: {title[:30]}")
        return True, "Task submitted successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def update_task(
    db: Session, 
    employee_id: str, 
    task_id: int, 
    title: str, 
    description: str, 
    status: str
) -> tuple[bool, str]:
    """
    Updates an employee's task.
    Allowed ONLY if the task was created TODAY.
    """
    task = get_task_by_id(db, task_id)
    if not task:
        return False, "Task not found"
        
    if task.employee_id != employee_id:
        return False, "Unauthorized: You can only edit your own tasks"
        
    # Business Rule: Allowed only if Task Date == Current Date
    if task.created_date != date.today():
        return False, "Security constraint violated: You can only edit today's tasks"
        
    if not title:
        return False, "Task title is required"
        
    try:
        task.title = title.strip()
        task.description = description.strip() if description else None
        task.status = status
        task.updated_time = datetime.now().time()
        
        db.commit()
        log_activity(db, employee_id, f"Updated task: {title[:30]}")
        return True, "Task updated successfully"
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"

def get_filtered_tasks(
    db: Session, 
    employee_id: str = None, 
    status_filter: str = None, 
    query_str: str = None,
    start_date: date = None,
    end_date: date = None
) -> list[Task]:
    """
    Advanced task filtering system.
    Supports filtering by Employee, Status, Text Search, and Date Range.
    """
    query = db.query(Task)
    
    # 1. Filter by employee
    if employee_id:
        query = query.filter(Task.employee_id == employee_id)
        
    # 2. Filter by status
    if status_filter and status_filter != 'All':
        query = query.filter(Task.status == status_filter)
        
    # 3. Filter by search query
    if query_str:
        pattern = f"%{query_str}%"
        query = query.filter(or_(Task.title.like(pattern), Task.description.like(pattern)))
        
    # 4. Filter by date range
    if start_date:
        query = query.filter(Task.created_date >= start_date)
    if end_date:
        query = query.filter(Task.created_date <= end_date)
        
    return query.order_by(Task.created_date.desc(), Task.created_time.desc()).all()

def get_tasks_by_period(db: Session, employee_id: str, period: str) -> list[Task]:
    """
    Filters tasks by historical time window presets:
    - yesterday
    - last_week
    - last_month
    - last_year
    """
    today = date.today()
    start_date = None
    end_date = today # Default to today
    
    if period == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif period == 'last_week':
        start_date = today - timedelta(days=7)
    elif period == 'last_month':
        start_date = today - timedelta(days=30)
    elif period == 'last_year':
        start_date = today - timedelta(days=365)
        
    return get_filtered_tasks(db, employee_id=employee_id, start_date=start_date, end_date=end_date)

def get_calendar_events(db: Session, employee_id: str) -> list[dict]:
    """
    Formats the employee's task submissions for visual rendering in a calendar.
    Returns a list of dicts: [{'date': 'YYYY-MM-DD', 'color': 'color', 'count': X, 'tasks': [...]}]
    """
    tasks = db.query(Task).filter(Task.employee_id == employee_id).all()
    
    # Group tasks by date
    grouped = {}
    for task in tasks:
        d_str = task.created_date.strftime('%Y-%m-%d')
        if d_str not in grouped:
            grouped[d_str] = []
        grouped[d_str].append(task)
        
    events = []
    for d_str, day_tasks in grouped.items():
        # Determine status representation
        statuses = [t.status for t in day_tasks]
        
        # Color strategy based on task completion
        if all(s == 'Completed' for s in statuses):
            color = '#10B981' # Emerald Green
            summary = 'Completed'
        elif any(s == 'Blocked' for s in statuses):
            color = '#EF4444' # Critical Red
            summary = 'Blocked'
        elif any(s == 'Work In Progress' for s in statuses):
            color = '#8B5CF6' # Indigo/Violet
            summary = 'In Progress'
        elif any(s == 'On Hold' for s in statuses):
            color = '#F59E0B' # Amber
            summary = 'On Hold'
        else:
            color = '#3B82F6' # Blue
            summary = 'Pending'
            
        events.append({
            'date': d_str,
            'title': f"{len(day_tasks)} Tasks: {summary}",
            'color': color,
            'textColor': 'white',
            'tasks': [{'title': t.title, 'status': t.status} for t in day_tasks]
        })
        
    return events
