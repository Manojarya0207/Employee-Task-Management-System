from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from validators.schemas import EmployeeCreateRequest, EmployeeUpdateRequest
from controllers.employee_controller import EmployeeController
from middlewares.auth_middleware import RoleChecker

router = APIRouter(prefix="/employees", tags=["Employees"], dependencies=[Depends(RoleChecker(["admin"]))])

@router.get("")
def get_all(db: Session = Depends(get_db)):
    return EmployeeController.get_all(db)

@router.get("/search")
def search(query: str, db: Session = Depends(get_db)):
    return EmployeeController.search(db, query)

@router.post("")
def add(req: EmployeeCreateRequest, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.add(
        db, current_user["employee_id"], req.employee_id, req.employee_name,
        req.phone_number, req.password, req.role, req.department, req.joining_date
    )
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.put("/{employee_id}")
def update(employee_id: str, req: EmployeeUpdateRequest, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.update(
        db, current_user["employee_id"], employee_id, req.employee_name,
        req.phone_number, req.department, req.status
    )
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.delete("/{employee_id}")
def delete(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.delete(db, current_user["employee_id"], employee_id)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/{employee_id}/reset-password")
def reset_password(employee_id: str, new_password: str, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.reset_password(db, current_user["employee_id"], employee_id, new_password)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/{employee_id}/toggle-status")
def toggle_status(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.toggle_status(db, current_user["employee_id"], employee_id)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.get("/registrations/pending")
def pending_registrations(db: Session = Depends(get_db)):
    return EmployeeController.get_pending_registrations(db)

@router.post("/registrations/{employee_id}/approve")
def approve_registration(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.approve_registration(db, current_user["employee_id"], employee_id)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/registrations/{employee_id}/reject")
def reject_registration(employee_id: str, reason: str = "", db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    res = EmployeeController.reject_registration(db, current_user["employee_id"], employee_id, reason)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])
