from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from validators.schemas import TaskCreateRequest, TaskUpdateRequest
from controllers.task_controller import TaskController
from middlewares.auth_middleware import get_current_user
from datetime import date

router = APIRouter(prefix="/tasks", tags=["Tasks"], dependencies=[Depends(get_current_user)])

@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    res = TaskController.get_by_id(db, task_id)
    if res["success"]:
        return res
    raise HTTPException(status_code=404, detail=res["message"])

@router.get("/employee/{employee_id}")
def get_employee_tasks(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Users can only view their own tasks, admins can view any
    if current_user["role"] != "admin" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return TaskController.get_employee_tasks(db, employee_id)

@router.post("")
def add_task(req: TaskCreateRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    res = TaskController.add(db, current_user["employee_id"], req.title, req.description, req.status)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.put("/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    res = TaskController.update(db, current_user["employee_id"], task_id, req.title, req.description, req.status)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.get("/filter/data")
def get_filtered(
    employee_id: str = None, 
    status: str = None, 
    query: str = None, 
    start_date: date = None, 
    end_date: date = None, 
    db: Session = Depends(get_db)
):
    return TaskController.get_filtered(db, employee_id, status, query, start_date, end_date)

@router.get("/period/{period}")
def get_by_period(period: str, employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return TaskController.get_by_period(db, employee_id, period)

@router.get("/calendar/{employee_id}")
def get_calendar_events(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return TaskController.get_calendar_events(db, employee_id)
