from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from controllers.dashboard_controller import DashboardController
from middlewares.auth_middleware import get_current_user, RoleChecker

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])

@router.get("/admin")
def get_admin_metrics(db: Session = Depends(get_db), current_user: dict = Depends(RoleChecker(["admin"]))):
    return DashboardController.get_admin_metrics(db)

@router.get("/employee/{employee_id}")
def get_employee_metrics(employee_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return DashboardController.get_employee_metrics(db, employee_id)
