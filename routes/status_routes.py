from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from controllers.status_controller import StatusController
from validators.schemas import StatusCreateRequest
from middlewares.auth_middleware import get_current_user, RoleChecker

router = APIRouter(prefix="/statuses", tags=["Statuses"], dependencies=[Depends(get_current_user)])

@router.get("/tasks")
def get_task_statuses(db: Session = Depends(get_db)):
    return StatusController.get_task_statuses(db)

@router.get("/employees")
def get_employee_statuses(db: Session = Depends(get_db)):
    return StatusController.get_employee_statuses(db)

@router.post("/tasks", dependencies=[Depends(RoleChecker(["admin"]))])
def add_task_status(req: StatusCreateRequest, db: Session = Depends(get_db)):
    res = StatusController.add_task_status(db, req.name, req.description, req.color)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/employees", dependencies=[Depends(RoleChecker(["admin"]))])
def add_employee_status(req: StatusCreateRequest, db: Session = Depends(get_db)):
    res = StatusController.add_employee_status(db, req.name, req.description, req.color)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.delete("/tasks/{name}", dependencies=[Depends(RoleChecker(["admin"]))])
def delete_task_status(name: str, db: Session = Depends(get_db)):
    res = StatusController.delete_task_status(db, name)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.delete("/employees/{name}", dependencies=[Depends(RoleChecker(["admin"]))])
def delete_employee_status(name: str, db: Session = Depends(get_db)):
    res = StatusController.delete_employee_status(db, name)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])
