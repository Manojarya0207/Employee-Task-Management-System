from nicegui import app, ui
from models import SessionLocal
from controllers.employee_controller import EmployeeController
from controllers.report_controller import ReportController
from pages.layout import render_layout
from datetime import date, datetime

def init_reports_routes():

    @ui.page('/admin/reports')
    def reports_page():
        # Authenticate and authorize admin
        if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
            ui.navigate.to('/login')
            return

        db = SessionLocal()
        try:
            # Query all employees for filter dropdown
            res_emp = EmployeeController.get_all(db)
            employees = res_emp["data"] if res_emp["success"] else []
            emp_choices = {'All': 'All Employees'}
            for e in employees:
                emp_choices[e['employee_id']] = f"{e['employee_name']} ({e['employee_id']})"
        finally:
            db.close()

        with render_layout('/admin/reports'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8 responsive-page-header'):
                with ui.element('div'):
                    ui.label('Analytics Reports').classes('text-slate-900 text-3xl font-bold tracking-tight')
                    ui.label('Filter, review, and export formatted worksheets and printable summaries').classes('text-gray-500 text-sm')

            # Controls grid
            with ui.element('div').classes('glass-card p-6 w-full mb-8'):
                ui.label('Report Configuration').classes('text-slate-900 text-lg font-semibold mb-6')
                
                with ui.grid().classes('grid-cols-1 md:grid-cols-4 gap-6 mb-6'):
                    
                    # 1. Report Type
                    rep_type = ui.select({
                        'daily': 'Daily Report (Today)',
                        'weekly': 'Weekly Report (7 Days)',
                        'monthly': 'Monthly Report (30 Days)',
                        'custom': 'Custom Date Range'
                    }, value='daily').classes('w-full').props('outlined')
                    
                    # 2. Status Filter
                    status_val = ui.select({
                        'All': 'All Statuses',
                        'Pending': 'Pending',
                        'Work In Progress': 'In Progress',
                        'Completed': 'Completed',
                        'Blocked': 'Blocked',
                        'On Hold': 'On Hold'
                    }, value='All').classes('w-full').props('outlined')

                    # 3. Employee Filter
                    emp_val = ui.select(emp_choices, value='All').classes('w-full').props('outlined')

                    # 4. Export Format
                    fmt_val = ui.select({
                        'csv': 'CSV Spreadsheet',
                        'excel': 'Excel Worksheet (.xlsx)',
                        'pdf': 'Printable PDF (.pdf)'
                    }, value='excel').classes('w-full').props('outlined')

                # Custom Date Range selection (shown only if rep_type == 'custom')
                date_row = ui.row().classes('w-full gap-6 items-center mb-6 responsive-date-row')
                
                with date_row:
                    start_input = ui.input('Start Date (YYYY-MM-DD)', value=date.today().strftime('%Y-%m-%d')).classes('w-64').props('outlined dense color=primary')
                    end_input = ui.input('End Date (YYYY-MM-DD)', value=date.today().strftime('%Y-%m-%d')).classes('w-64').props('outlined dense color=primary')

                # Visibility logic for custom dates
                def handle_type_change():
                    if rep_type.value == 'custom':
                        date_row.set_visibility(True)
                    else:
                        date_row.set_visibility(False)
                        
                rep_type.on('change', handle_type_change)
                handle_type_change() # Trigger initial visibility

                # Trigger Button
                def run_export():
                    r_type = rep_type.value
                    s_date_str = start_input.value
                    e_date_str = end_input.value
                    s_emp = emp_val.value
                    s_status = status_val.value
                    s_fmt = fmt_val.value
                    
                    # Date formatting
                    s_date, e_date = None, None
                    if r_type == 'custom':
                        try:
                            s_date = datetime.strptime(s_date_str, '%Y-%m-%d').date()
                            e_date = datetime.strptime(e_date_str, '%Y-%m-%d').date()
                        except Exception as e:
                            ui.notify('Invalid Date Format. Please use YYYY-MM-DD', type='negative')
                            return
                            
                    db_session = SessionLocal()
                    try:
                        # Fetch report data
                        res = ReportController.get_report_data(
                            db=db_session,
                            report_type=r_type,
                            start_date=s_date,
                            end_date=e_date,
                            employee_id=s_emp,
                            status=s_status
                        )
                        
                        if not res["success"] or not res["data"]:
                            ui.notify('No records found matching current configuration criteria.', type='warning')
                            return
                            
                        report_data = res["data"]
                        title = f"{r_type.upper()} REPORT"
                        if r_type == 'custom':
                            title = f"CUSTOM REPORT ({s_date_str} to {e_date_str})"
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        if s_fmt == 'csv':
                            buffer = ReportController.export_csv(db_session, r_type, s_date, e_date, s_emp, s_status)
                            ui.download(buffer.getvalue(), filename=f"taskflow_report_{timestamp}.csv")
                            ui.notify('CSV report generated and download initiated.', type='positive')
                            
                        elif s_fmt == 'excel':
                            buffer = ReportController.export_excel(db_session, r_type, s_date, e_date, s_emp, s_status, title)
                            ui.download(buffer.getvalue(), filename=f"taskflow_report_{timestamp}.xlsx")
                            ui.notify('Excel report generated and download initiated.', type='positive')
                            
                        elif s_fmt == 'pdf':
                            buffer = ReportController.export_pdf(db_session, r_type, s_date, e_date, s_emp, s_status, title)
                            ui.download(buffer.getvalue(), filename=f"taskflow_report_{timestamp}.pdf")
                            ui.notify('PDF report generated and download initiated.', type='positive')
                            
                    except Exception as err:
                        ui.notify(f"Generation error: {str(err)}", type='negative')
                    finally:
                        db_session.close()

                with ui.row().classes('w-full justify-end mt-4 responsive-actions'):
                    ui.button('Generate & Export Report', icon='summarize', on_click=run_export).classes('btn-neon').props('size=lg')
