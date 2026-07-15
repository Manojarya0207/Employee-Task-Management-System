from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models import get_db
from controllers.report_controller import ReportController
from middlewares.auth_middleware import RoleChecker
from datetime import date

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(RoleChecker(["admin"]))])

@router.get("/data")
def get_report_data(
    report_type: str, 
    start_date: date = None, 
    end_date: date = None, 
    employee_id: str = None, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    return ReportController.get_report_data(db, report_type, start_date, end_date, employee_id, status)

@router.get("/export/csv")
def export_csv(
    report_type: str, 
    start_date: date = None, 
    end_date: date = None, 
    employee_id: str = None, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    buffer = ReportController.export_csv(db, report_type, start_date, end_date, employee_id, status)
    return StreamingResponse(
        buffer, 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=report.csv"}
    )

@router.get("/export/excel")
def export_excel(
    report_type: str, 
    start_date: date = None, 
    end_date: date = None, 
    employee_id: str = None, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    buffer = ReportController.export_excel(db, report_type, start_date, end_date, employee_id, status)
    return StreamingResponse(
        buffer, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=report.xlsx"}
    )

@router.get("/export/pdf")
def export_pdf(
    report_type: str, 
    start_date: date = None, 
    end_date: date = None, 
    employee_id: str = None, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    buffer = ReportController.export_pdf(db, report_type, start_date, end_date, employee_id, status)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )
