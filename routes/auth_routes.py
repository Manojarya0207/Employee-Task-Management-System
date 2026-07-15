from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import get_db
from validators.schemas import LoginRequest, RegisterRequest, ChangePasswordRequest
from controllers.auth_controller import AuthController
from utils.jwt_utils import sign_token
from middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    res = AuthController.login(db, req.employee_id, req.password)
    if res["success"]:
        # Sign token
        token = sign_token(res["data"])
        res["data"]["token"] = token
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    res = AuthController.register(db, req.employee_name, req.phone_number, req.password, req.department)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    res = AuthController.change_password(db, current_user["employee_id"], req.old_password, req.new_password)
    if res["success"]:
        return res
    raise HTTPException(status_code=400, detail=res["message"])

@router.get("/registration-status/{employee_id}")
def check_status(employee_id: str, db: Session = Depends(get_db)):
    res = AuthController.get_registration_status(db, employee_id)
    if res["success"]:
        return res
    raise HTTPException(status_code=404, detail=res["message"])
