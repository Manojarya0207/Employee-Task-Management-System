from sqlalchemy.orm import Session
from services import report_service

class ReportController:
    @staticmethod
    def get_report_data(db: Session, report_type: str, start_date = None, end_date = None, employee_id: str = None, status: str = None) -> dict:
        data = report_service.fetch_report_data(db, report_type, start_date, end_date, employee_id, status)
        return {
            "success": True,
            "message": "Report data fetched",
            "data": data
        }

    @staticmethod
    def export_csv(db: Session, report_type: str, start_date = None, end_date = None, employee_id: str = None, status: str = None):
        data = report_service.fetch_report_data(db, report_type, start_date, end_date, employee_id, status)
        return report_service.export_csv(data)

    @staticmethod
    def export_excel(db: Session, report_type: str, start_date = None, end_date = None, employee_id: str = None, status: str = None, title: str = "Report"):
        data = report_service.fetch_report_data(db, report_type, start_date, end_date, employee_id, status)
        return report_service.export_excel(data, title)

    @staticmethod
    def export_pdf(db: Session, report_type: str, start_date = None, end_date = None, employee_id: str = None, status: str = None, title: str = "Report"):
        data = report_service.fetch_report_data(db, report_type, start_date, end_date, employee_id, status)
        return report_service.export_pdf(data, title)
