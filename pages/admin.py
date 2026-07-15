from nicegui import app, ui
from models import SessionLocal
from models.employee import Employee
from models.task import Task
from models.activity_log import ActivityLog
from services.employee_service import (
    get_all_employees, search_employees, add_employee,
    update_employee, toggle_employee_status, reset_employee_password,
    delete_employee
)
from services.auth_service import log_activity
from services.registration_service import (
    get_all_registration_requests,
    count_pending_requests,
    approve_employee,
    reject_employee,
)
from pages.layout import render_layout
from datetime import date, datetime, timedelta
from sqlalchemy import func
import os

# Constants to avoid duplicated string literal smells
STATUS_COMPLETED = 'Completed'
STATUS_PENDING = 'Pending'
STATUS_WIP = 'Work In Progress'
STATUS_BLOCKED = 'Blocked'
STATUS_HOLD = 'On Hold'

PATH_LOGIN = '/login'
PATH_ADMIN = '/admin'
PATH_ADMIN_EMPLOYEES = '/admin/employees'

ROLE_ADMIN = 'admin'
ROLE_EMPLOYEE = 'employee'

CLASS_GLASS_CARD_METRIC = 'glass-card p-6 metric-card'
CLASS_GLASS_CARD_WFULL = 'glass-card p-6 w-full'
CLASS_WFULL_ITEMS_JUSTIFY_MB8 = 'w-full items-center justify-between mb-8'
CLASS_WFULL_JUSTIFY_END_GAP2 = 'w-full justify-end mt-4 gap-2'
CLASS_TEXT_GRAY_500_SM = 'text-gray-500 text-sm'
CLASS_TEXT_GRAY_500_SM_BOLD = 'text-gray-500 text-sm font-semibold'
CLASS_TEXT_GRAY_500_XS_MT1 = 'text-gray-500 text-xs mt-1'
CLASS_WFULL_MB3 = 'w-full mb-3'

TIME_FORMAT_12H = '%I:%M %p'
DATE_FORMAT = '%Y-%m-%d'

def init_admin_routes():
    pass

@ui.page('/admin')
def admin_dashboard():
    # Authenticate and authorize admin role
    if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != ROLE_ADMIN:
        ui.navigate.to(PATH_LOGIN)
        return
        
    db = SessionLocal()
    try:
        today = date.today()
        
        # 1. Gather Statistics
        total_employees = db.query(Employee).count()
        inactive_employees = db.query(Employee).filter(Employee.status == 'inactive').count()
        
        today_tasks = db.query(Task).filter(Task.created_date == today).all()
        today_count = len(today_tasks)
        
        completed_today = sum(1 for t in today_tasks if t.status == STATUS_COMPLETED)
        wip_today = sum(1 for t in today_tasks if t.status == STATUS_WIP)
        pending_today = sum(1 for t in today_tasks if t.status == STATUS_PENDING)
        blocked_today = sum(1 for t in today_tasks if t.status == STATUS_BLOCKED)
        on_hold_today = sum(1 for t in today_tasks if t.status == STATUS_HOLD)
        
        # Completion Percentage
        completion_rate = round((completed_today / today_count) * 100) if today_count > 0 else 0
        
        # Recent Tasks Uploaded (last 8)
        recent_tasks = db.query(Task, Employee)\
            .join(Employee, Task.employee_id == Employee.employee_id)\
            .order_by(Task.last_modified.desc())\
            .limit(8).all()
            
        # Chart Data - Last 7 Days Activity
        days_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
        days_labels = [d.strftime('%a %d') for d in days_7]
        daily_counts = []
        for d in days_7:
            c = db.query(Task).filter(Task.created_date == d).count()
            daily_counts.append(c)

    finally:
        db.close()
        
    # Draw Layout
    with render_layout(PATH_ADMIN):
        # Header
        with ui.row().classes(CLASS_WFULL_ITEMS_JUSTIFY_MB8):
            with ui.element('div'):
                ui.label('Admin Dashboard').classes('text-3xl font-bold tracking-tight')
                ui.label('Overview of company task progress and employee status').classes(CLASS_TEXT_GRAY_500_SM)
            
            # Backup database action button
            def download_db():
                db_path = '/Users/manojsarya/Documents/ATS Projects/Employee-Task-Management-System/database/taskflow.db'
                if os.path.exists(db_path):
                    ui.download(db_path, filename='taskflow_backup.db')
                    ui.notify('Database backup downloaded successfully!', type='positive')
                else:
                    ui.notify('Backup file not found', type='negative')
            
            ui.button('Backup Database', icon='cloud_download', on_click=download_db).classes('btn-neon')

        # 2. Metric Cards Grid
        with ui.grid().classes('grid-cols-1 md:grid-cols-4 gap-6 mb-8 w-full'):
            
            # Card 1: Total Employees
            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                with ui.row().classes('justify-between items-center'):
                    ui.label('Total Employees').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                    ui.element('i').classes('ri-group-line text-primary text-2xl')
                ui.label(str(total_employees)).classes('text-4xl font-bold mt-2')
                ui.label(f"{inactive_employees} inactive accounts").classes('text-gray-500 text-xs mt-1')

            # Card 2: Today's Tasks
            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                with ui.row().classes('justify-between items-center'):
                    ui.label('Today\'s Submissions').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                    ui.element('i').classes('ri-file-list-3-line text-primary text-2xl')
                ui.label(str(today_count)).classes('text-4xl font-bold mt-2')
                ui.label(f"{pending_today} pending | {wip_today} in progress").classes('text-gray-500 text-xs mt-1')

            # Card 3: Completion Rate
            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                with ui.row().classes('justify-between items-center'):
                    ui.label('Completion Rate').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                    ui.element('i').classes('ri-pie-chart-line text-emerald-600 text-2xl')
                ui.label(f"{completion_rate}%").classes('text-emerald-600 text-4xl font-bold mt-2')
                ui.label(f"{completed_today} completed tasks today").classes('text-gray-500 text-xs mt-1')

            # Card 4: Action Blockers
            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                with ui.row().classes('justify-between items-center'):
                    ui.label('Blocked & Hold').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                    ui.element('i').classes('ri-error-warning-line text-red-600 text-2xl')
                ui.label(str(blocked_today + on_hold_today)).classes('text-red-600 text-4xl font-bold mt-2')
                ui.label(f"{blocked_today} blocked | {on_hold_today} on hold").classes('text-gray-500 text-xs mt-1')

        # 3. Interactive Charts Grid (ECharts)
        with ui.grid().classes('grid-cols-1 md:grid-cols-3 gap-6 mb-8 w-full'):
            
            # Chart 1: Daily Submissions History
            with ui.element('div').classes('glass-card p-6 col-span-2'):
                ui.label('Task Activity (Last 7 Days)').classes('text-lg font-semibold mb-4')
                
                chart_options = {
                    'backgroundColor': 'transparent',
                    'tooltip': {'trigger': 'axis', 'backgroundColor': '#1E293B', 'textStyle': {'color': '#FFF'}},
                    'xAxis': {
                        'type': 'category',
                        'data': days_labels,
                        'axisLabel': {'color': '#475569'},
                        'axisLine': {'lineStyle': {'color': '#E2E8F0'}}
                    },
                    'yAxis': {
                        'type': 'value',
                        'axisLabel': {'color': '#475569'},
                        'splitLine': {'lineStyle': {'color': '#F1F5F9'}}
                    },
                    'series': [{
                        'data': daily_counts,
                        'type': 'bar',
                        'barWidth': '40%',
                        'itemStyle': {
                            'color': {
                                'type': 'linear',
                                'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                'colorStops': [
                                    {'offset': 0, 'color': '#14b8a6'},
                                    {'offset': 1, 'color': '#2563eb'}
                                ]
                            },
                            'borderRadius': [4, 4, 0, 0]
                        }
                    }]
                }
                ui.echart(options=chart_options).classes('w-full h-64')

            # Chart 2: Status Distribution
            with ui.element('div').classes('dark-card p-6'):
                ui.label('Status Distribution (Today)').classes('text-lg font-semibold mb-4')
                
                pie_options = {
                    'backgroundColor': 'transparent',
                    'tooltip': {'trigger': 'item', 'backgroundColor': '#1E293B', 'textStyle': {'color': '#FFF'}},
                    'legend': {
                        'orient': 'horizontal',
                        'bottom': '18',
                        'left': 'center',
                        'itemGap': 30,
                        'itemWidth': 18,
                        'itemHeight': 10,
                        'textStyle': {'color': '#64727f', 'fontSize': 13, 'padding': [0, 8, 0, 4]}
                    },
                    'series': [{
                        'name': 'Tasks',
                        'type': 'pie',
                        'radius': ['34%', '58%'],
                        'center': ['50%', '42%'],
                        'avoidLabelOverlap': False,
                        'itemStyle': {'borderRadius': 6, 'borderColor': '#ffffff', 'borderWidth': 3},
                        'label': {'show': False},
                        'labelLine': {'show': False},
                        'emphasis': {'label': {'show': False}},
                        'data': [
                            {'value': completed_today, 'name': 'Completed', 'itemStyle': {'color': '#20c997'}},
                            {'value': wip_today, 'name': 'In Progress', 'itemStyle': {'color': '#8b5cf6'}},
                            {'value': pending_today, 'name': STATUS_PENDING, 'itemStyle': {'color': '#3b82f6'}},
                            {'value': blocked_today, 'name': STATUS_BLOCKED, 'itemStyle': {'color': '#ef4444'}},
                            {'value': on_hold_today, 'name': STATUS_HOLD, 'itemStyle': {'color': '#f59e0b'}}
                        ]
                    }]
                }
                ui.echart(options=pie_options).classes('w-full h-80')

        # 4. Recent Task Submissions
        with ui.element('div').classes(CLASS_GLASS_CARD_WFULL):
            ui.label('Recent Employee Task Updates').classes('text-lg font-semibold mb-4')
            
            with ui.element('div').classes('overflow-x-auto w-full'):
                with ui.element('table').classes('w-full text-left text-sm border-collapse'):
                    # Table Header
                    with ui.element('tr').classes('bg-slate-100 text-slate-900 font-semibold border-b border-slate-200'):
                        with ui.element('th').classes('p-3'):
                            ui.label('Date & Time')
                        with ui.element('th').classes('p-3'):
                            ui.label('Employee')
                        with ui.element('th').classes('p-3'):
                            ui.label('Task Title')
                        with ui.element('th').classes('p-3'):
                            ui.label('Status')
                    
                    # Table Body
                    for task, emp in recent_tasks:
                        with ui.element('tr').classes('border-b border-slate-100 hover:bg-slate-50'):
                            with ui.element('td').classes('p-3 text-gray-500'):
                                ui.label(f"{task.created_date.strftime(DATE_FORMAT)} {task.created_time.strftime(TIME_FORMAT_12H)}")
                            with ui.element('td').classes('p-3 font-semibold'):
                                ui.label(f"{emp.employee_name} ({emp.employee_id})")
                            with ui.element('td').classes('p-3 text-gray-700'):
                                ui.label(task.title)
                            with ui.element('td').classes('p-3'):
                                status_map = {
                                    STATUS_COMPLETED: 'completed',
                                    STATUS_WIP: 'wip',
                                    STATUS_BLOCKED: 'blocked',
                                    STATUS_HOLD: 'hold'
                                }
                                badge_class = status_map.get(task.status, 'pending')
                                ui.html(f'<span class="badge-status badge-{badge_class}">{task.status}</span>')


@ui.page(PATH_ADMIN_EMPLOYEES)
def employee_management(action: str = None):
    # Authenticate and authorize admin
    if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != ROLE_ADMIN:
        ui.navigate.to(PATH_LOGIN)
        return

    # Fetch pending registration count for the tab badge
    db_p = SessionLocal()
    try:
        pending_count = count_pending_requests(db_p)
    finally:
        db_p.close()

    if action == 'add':
        with render_layout(PATH_ADMIN_EMPLOYEES, action=action):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label('Add New Employee').classes('text-3xl font-bold tracking-tight')
                    ui.label('Create a new employee user account and allocate department').classes('text-gray-500 text-sm')
            
            with ui.element('div').classes('glass-card p-8 w-full mt-6'):
                with ui.row().classes('items-center mb-6 gap-3'):
                    ui.element('i').classes('ri-user-add-line text-primary text-3xl')
                    with ui.element('div'):
                        ui.label('Employee Credentials & Allocation').classes('text-lg font-bold')
                        ui.label('Please enter the employee information below. All fields with * are required.').classes('text-xs text-gray-500')
                
                submit_btn = None

                with ui.grid().classes('grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 w-full'):
                    with ui.element('div'):
                        ui.label('Employee ID *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_id = ui.input(placeholder='Auto-generated ID').classes('w-full').props('outlined color=primary dense readonly')
                        e_id_hint = ui.label('Generated from Name + Phone').classes('text-xs mt-1 text-gray-500')
                    
                    with ui.element('div'):
                        ui.label('Full Name *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_name = ui.input(placeholder='e.g. John Doe').classes('w-full').props('outlined color=primary dense')
                        e_name_hint = ui.label('Minimum 3 characters required').classes('text-xs mt-1 text-gray-500')

                    with ui.element('div'):
                        ui.label('Phone Number *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_phone = ui.input(placeholder='10-digit mobile number').classes('w-full').props('outlined color=primary dense maxlength=10')
                        e_phone_hint = ui.label('Exactly 10 digits required').classes('text-xs mt-1 text-gray-500')

                    with ui.element('div'):
                        ui.label('Department *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_dept = ui.select({
                            '': 'Select department',
                            'AI / ML': 'AI / ML',
                            'IoT': 'IoT',
                            'Robotics': 'Robotics',
                            'AR / VR': 'AR / VR',
                            'Others': 'Others'
                        }, value='').classes('w-full').props('outlined dense')
                        e_dept_hint = ui.label('Please select a department').classes('text-xs mt-1 text-gray-500')

                    with ui.element('div').classes('col-span-1 md:col-span-2'):
                        e_dept_other = ui.input(placeholder='Specify custom department name').classes('w-full').props('outlined color=primary dense').bind_visibility_from(e_dept, 'value', value='Others')

                    with ui.element('div'):
                        ui.label('Role *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_role = ui.select({'employee': 'Employee', 'admin': 'Administrator'}, value='employee').classes('w-full').props('outlined dense')

                    with ui.element('div'):
                        ui.label('Joining Date *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_join = ui.input(value=date.today().strftime('%Y-%m-%d')).classes('w-full').props('outlined color=primary dense type=date')

                    with ui.element('div'):
                        ui.label('Password *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_password = ui.input(placeholder='Minimum 6 characters', password=True, password_toggle_button=True).classes('w-full').props('outlined color=primary dense')
                        e_password_hint = ui.label('Minimum 6 characters required').classes('text-xs mt-1 text-gray-500')

                    with ui.element('div'):
                        ui.label('Confirm Password *').classes('text-xs font-semibold text-slate-700 mb-1')
                        e_confirm_password = ui.input(placeholder='Re-enter password', password=True, password_toggle_button=True).classes('w-full').props('outlined color=primary dense')
                        e_confirm_password_hint = ui.label('Passwords must match').classes('text-xs mt-1 text-gray-500')

                def update_generated_id():
                    import re
                    name = e_name.value or ''
                    name_letters = re.sub(r'[^a-zA-Z]', '', name).upper()
                    name_part = name_letters[:4] if len(name_letters) >= 4 else name_letters
                    
                    phone = e_phone.value or ''
                    phone_digits = re.sub(r'\D', '', phone)
                    phone_part = phone_digits[:4] if len(phone_digits) >= 4 else phone_digits
                    
                    e_id.set_value(f"{name_part}{phone_part}")
                    
                    # Run validations
                    validate_fields()

                def validate_fields():
                    import re
                    name = e_name.value or ''
                    if re.search(r'\d', name):
                        e_name_hint.set_text('✗ Name field does not allow numbers/digits')
                        e_name_hint.classes(replace='text-xs mt-1 text-red-600')
                        name_ok = False
                    elif re.search(r'[^a-zA-Z\s]', name):
                        e_name_hint.set_text('✗ Name field does not allow special characters')
                        e_name_hint.classes(replace='text-xs mt-1 text-red-600')
                        name_ok = False
                    elif len(name.strip()) >= 3:
                        e_name_hint.set_text('✓ Name is valid')
                        e_name_hint.classes(replace='text-xs mt-1 text-emerald-600')
                        name_ok = True
                    else:
                        e_name_hint.set_text('✗ Name must be at least 3 characters')
                        e_name_hint.classes(replace='text-xs mt-1 text-red-600')
                        name_ok = False

                    phone = e_phone.value or ''
                    if re.search(r'\D', phone):
                        e_phone_hint.set_text('✗ Phone number does not allow letters or text')
                        e_phone_hint.classes(replace='text-xs mt-1 text-red-600')
                        phone_ok = False
                    elif len(phone) == 10:
                        s_db = SessionLocal()
                        try:
                            phone_exists = s_db.query(Employee).filter(Employee.phone_number == phone).first()
                            if phone_exists:
                                e_phone_hint.set_text('✗ Phone number is already registered')
                                e_phone_hint.classes(replace='text-xs mt-1 text-red-600')
                                phone_ok = False
                            else:
                                e_phone_hint.set_text('✓ Phone number is valid and unique')
                                e_phone_hint.classes(replace='text-xs mt-1 text-emerald-600')
                                phone_ok = True
                        finally:
                            s_db.close()
                    else:
                        e_phone_hint.set_text('✗ Phone number must be exactly 10 digits')
                        e_phone_hint.classes(replace='text-xs mt-1 text-red-600')
                        phone_ok = False

                    dept = e_dept.value or ''
                    if dept == 'Others':
                        dept_val = e_dept_other.value or ''
                        if len(dept_val.strip()) >= 2:
                            e_dept_hint.set_text('✓ Department details provided')
                            e_dept_hint.classes(replace='text-xs mt-1 text-emerald-600')
                            dept_ok = True
                        else:
                            e_dept_hint.set_text('✗ Custom department must be at least 2 characters')
                            e_dept_hint.classes(replace='text-xs mt-1 text-red-600')
                            dept_ok = False
                    elif dept != '':
                        e_dept_hint.set_text('✓ Department selected')
                        e_dept_hint.classes(replace='text-xs mt-1 text-emerald-600')
                        dept_ok = True
                    else:
                        e_dept_hint.set_text('✗ Please select a department')
                        e_dept_hint.classes(replace='text-xs mt-1 text-red-600')
                        dept_ok = False

                    pwd = e_password.value or ''
                    if len(pwd) >= 6:
                        e_password_hint.set_text('✓ Password is valid')
                        e_password_hint.classes(replace='text-xs mt-1 text-emerald-600')
                        pwd_ok = True
                    else:
                        e_password_hint.set_text('✗ Password must be at least 6 characters')
                        e_password_hint.classes(replace='text-xs mt-1 text-red-600')
                        pwd_ok = False

                    confirm = e_confirm_password.value or ''
                    if confirm:
                        if pwd == confirm:
                            e_confirm_password_hint.set_text('✓ Passwords match')
                            e_confirm_password_hint.classes(replace='text-xs mt-1 text-emerald-600')
                            confirm_ok = True
                        else:
                            e_confirm_password_hint.set_text('✗ Passwords do not match')
                            e_confirm_password_hint.classes(replace='text-xs mt-1 text-red-600')
                            confirm_ok = False
                    else:
                        e_confirm_password_hint.set_text('Passwords must match')
                        e_confirm_password_hint.classes(replace='text-xs mt-1 text-gray-500')
                        confirm_ok = False

                    if submit_btn:
                        all_ok = name_ok and phone_ok and dept_ok and pwd_ok and confirm_ok
                        if all_ok:
                            submit_btn.props(remove='disable')
                        else:
                            submit_btn.props('disable')

                e_name.on_value_change(update_generated_id)
                e_phone.on_value_change(update_generated_id)
                e_dept.on_value_change(update_generated_id)
                e_dept_other.on_value_change(update_generated_id)
                e_password.on_value_change(update_generated_id)
                e_confirm_password.on_value_change(update_generated_id)

                def save():
                    try:
                        join_date = datetime.strptime(e_join.value, '%Y-%m-%d').date()
                    except:
                        join_date = date.today()
                        
                    s_db = SessionLocal()
                    try:
                        dept_val = e_dept_other.value.strip() if e_dept.value == 'Others' else e_dept.value
                        ok, msg = add_employee(
                            db=s_db,
                            creator_id=app.storage.user.get('employee_id'),
                            employee_id=e_id.value,
                            employee_name=e_name.value,
                            phone_number=e_phone.value,
                            password=e_password.value if e_password.value else e_id.value,
                            role=e_role.value,
                            department=dept_val,
                            joining_date=join_date
                        )
                        if ok:
                            ui.notify(msg, type='positive')
                            ui.navigate.to('/admin/employees')
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        s_db.close()

                with ui.row().classes('w-full justify-end mt-6 gap-3'):
                    ui.button('Cancel', on_click=lambda: ui.navigate.to('/admin/employees')).props('flat color=primary')
                    submit_btn = ui.button('Create Account', on_click=save).classes('btn-neon').props('disable')
        return

    # Renders the main wrapping page layout
    with render_layout(PATH_ADMIN_EMPLOYEES, action=action):

        # Helper method to render a pending/rejected request card
        def _render_request_card(emp, status):
            initials = ''.join(p[0].upper() for p in emp.employee_name.split()[:2])
            
            with ui.element('div').classes('glass-card p-5 flex flex-col gap-3'):
                # Avatar + Name
                with ui.row().classes('items-center gap-3 mb-1'):
                    with ui.element('div').classes(
                        'w-12 h-12 rounded-full flex items-center justify-center font-bold text-white text-lg flex-shrink-0'
                    ).style('background: linear-gradient(135deg, #0f766e, #2563eb)'):
                        ui.label(initials)
                    with ui.element('div').classes('flex-1 min-w-0'):
                        ui.label(emp.employee_name).classes('font-bold text-base truncate')
                        if status == 'pending':
                            ui.html('<span class="badge-status badge-pending" style="font-size:0.7rem">⏳ Pending</span>')
                        else:
                            ui.html('<span class="badge-status badge-blocked" style="font-size:0.7rem">❌ Rejected</span>')
                            
                # Info Fields
                with ui.element('div').classes('space-y-1 text-sm'):
                    with ui.row().classes('items-center gap-2'):
                        ui.element('i').classes('ri-id-card-line text-primary text-base')
                        ui.label('Employee ID:').classes('text-gray-500 text-xs')
                        ui.label(emp.employee_id).classes('font-mono font-semibold text-primary')
                    with ui.row().classes('items-center gap-2'):
                        ui.element('i').classes('ri-phone-line text-primary text-base')
                        ui.label('Phone:').classes('text-gray-500 text-xs')
                        ui.label(emp.phone_number).classes('font-medium')
                    with ui.row().classes('items-center gap-2'):
                        ui.element('i').classes('ri-calendar-line text-primary text-base')
                        ui.label('Registered:').classes('text-gray-500 text-xs')
                        reg_date = emp.created_at.strftime('%d %b %Y, %I:%M %p') if emp.created_at else 'Unknown'
                        ui.label(reg_date).classes('text-gray-700 text-xs')
                    if status == 'rejected':
                        if emp.rejected_at:
                            with ui.row().classes('items-center gap-2'):
                                ui.element('i').classes('ri-close-line text-red-500 text-base')
                                ui.label('Rejected:').classes('text-gray-500 text-xs')
                                ui.label(emp.rejected_at.strftime('%d %b %Y')).classes('text-red-500 text-xs font-medium')
                        if emp.rejection_reason:
                            with ui.element('div').classes('bg-red-50 border border-red-100 rounded-lg p-2 mt-1 w-full'):
                                ui.label('Reason:').classes('text-xs text-red-500 font-semibold')
                                ui.label(emp.rejection_reason).classes('text-xs text-red-700')
                                
                # Action buttons
                if status == 'pending':
                    _emp_id = emp.employee_id
                    _emp_name = emp.employee_name
                    with ui.row().classes('gap-2 mt-2 pt-3 border-t border-slate-100 w-full'):
                        def do_approve(eid=_emp_id):
                            a_db = SessionLocal()
                            try:
                                ok, msg = approve_employee(a_db, admin_id=app.storage.user.get('employee_id'), employee_id=eid)
                                ui.notify(msg, type='positive' if ok else 'negative')
                                if ok:
                                    ui.navigate.to('/admin/employees')
                            finally:
                                a_db.close()
                        ui.button('Approve', icon='check_circle', on_click=lambda eid=_emp_id: do_approve(eid))\
                            .classes('flex-1 text-sm')\
                            .props('color=positive unelevated')
                            
                        def do_reject_dialog(eid=_emp_id, ename=_emp_name):
                            with ui.dialog() as reject_dlg, ui.card().classes('glass-card p-6 w-96'):
                                ui.label(f'Reject: {ename}').classes('text-lg font-bold mb-2')
                                ui.label('Are you sure you want to reject this registration?').classes('text-gray-500 text-sm mb-4')
                                reason_input = ui.input(label='Reason for rejection (optional)').classes('w-full mb-4').props('outlined color=negative')
                                def confirm_reject(rid=eid):
                                    r_db = SessionLocal()
                                    try:
                                        ok, msg = reject_employee(r_db, admin_id=app.storage.user.get('employee_id'), employee_id=rid, reason=reason_input.value)
                                        ui.notify(msg, type='positive' if ok else 'negative')
                                        if ok:
                                            reject_dlg.close()
                                            ui.navigate.to('/admin/employees')
                                    finally:
                                        r_db.close()
                                with ui.row().classes('w-full justify-end gap-2'):
                                    ui.button('Cancel', on_click=reject_dlg.close).props('flat color=primary')
                                    ui.button('Reject', icon='cancel', on_click=lambda rid=eid: confirm_reject(rid)).props('color=negative unelevated')
                            reject_dlg.open()
                        ui.button('Reject', icon='cancel', on_click=lambda eid=_emp_id, ename=_emp_name: do_reject_dialog(eid, ename))\
                            .classes('flex-1 text-sm')\
                            .props('color=negative unelevated')
                elif status == 'rejected':
                    _emp_id = emp.employee_id
                    with ui.row().classes('gap-2 mt-2 pt-3 border-t border-slate-100 w-full justify-end'):
                        def do_reaccept(eid=_emp_id):
                            r_db = SessionLocal()
                            try:
                                ok, msg = approve_employee(r_db, admin_id=app.storage.user.get('employee_id'), employee_id=eid)
                                ui.notify(msg, type='positive' if ok else 'negative')
                                if ok:
                                    ui.navigate.to('/admin/employees')
                            finally:
                                r_db.close()
                        ui.button('reAccept', icon='check_circle', on_click=lambda eid=_emp_id: do_reaccept(eid))\
                            .classes('text-xs px-3 py-1')\
                            .props('color=positive flat dense')
        
        # Header
        with ui.row().classes('w-full items-center justify-between mb-8'):
            with ui.element('div'):
                ui.label('Employee Registry & Requests').classes('text-3xl font-bold tracking-tight')
                ui.label('Manage staff credentials, department allocations, and registration requests').classes('text-gray-500 text-sm')

        # Tabs Strip
        with ui.tabs().classes('w-full mb-6 border-b border-slate-200') as tabs:
            active_tab = ui.tab('active', label='Active Registry').props('icon=group')
            pending_label = f'Pending Requests ({pending_count})' if pending_count > 0 else 'Pending Requests'
            pending_tab = ui.tab('pending', label=pending_label).props('icon=pending_actions')
            rejected_tab = ui.tab('rejected', label='Rejected Requests').props('icon=cancel')

        stored_tab = app.storage.user.get('admin_employees_tab', 'active')
        tabs.value = stored_tab
        tabs.on_value_change(lambda e: app.storage.user.update(admin_employees_tab=e.value))

        with ui.tab_panels(tabs, value=stored_tab).classes('w-full bg-transparent'):
            
            # ── Panel 1: Active Registry ─────────────────────────────────
            with ui.tab_panel('active').classes('p-0 bg-transparent'):
                # Search bar & Add Button
                with ui.row().classes('w-full mb-6 items-center justify-between'):
                    with ui.row().classes('items-center gap-3'):
                        search_input = ui.input(placeholder='Search by ID, Name, Phone or Department...').classes('w-96').props('outlined dense color=primary')
                        
                        def run_search():
                            q = search_input.value
                            s_db = SessionLocal()
                            try:
                                res = search_employees(s_db, q)
                                table.rows = [{
                                    'employee_id': emp.employee_id,
                                    'employee_name': emp.employee_name,
                                    'phone_number': f"{emp.phone_number[:5]} {emp.phone_number[5:]}" if emp.phone_number and len(emp.phone_number) == 10 else (emp.phone_number or 'N/A'),
                                    'role': emp.role,
                                    'department': emp.department or 'N/A',
                                    'joining_date': emp.joining_date.strftime('%d %b %Y') if emp.joining_date else 'N/A',
                                    'status': emp.status
                                } for emp in res]
                            finally:
                                s_db.close()
                                
                        search_input.on('change', run_search)
                        ui.button('Search', icon='search', on_click=run_search).props('flat color=primary')

                # 3. Employee Grid Table
                columns = [
                    {'name': 'employee_id', 'label': 'Employee ID', 'field': 'employee_id', 'required': True, 'align': 'left', 'sortable': True},
                    {'name': 'employee_name', 'label': 'Name', 'field': 'employee_name', 'align': 'left', 'sortable': True},
                    {'name': 'phone_number', 'label': 'Phone Number', 'field': 'phone_number', 'align': 'left'},
                    {'name': 'role', 'label': 'Role', 'field': 'role', 'align': 'center', 'sortable': True},
                    {'name': 'department', 'label': 'Department', 'field': 'department', 'align': 'left', 'sortable': True},
                    {'name': 'joining_date', 'label': 'Joining Date', 'field': 'joining_date', 'align': 'center', 'sortable': True},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                ]

                # Load initial rows for approved/active employees
                db = SessionLocal()
                try:
                    employees = get_all_employees(db)
                    rows = [{
                        'employee_id': emp.employee_id,
                        'employee_name': emp.employee_name,
                        'phone_number': f"{emp.phone_number[:5]} {emp.phone_number[5:]}" if emp.phone_number and len(emp.phone_number) == 10 else (emp.phone_number or 'N/A'),
                        'role': emp.role,
                        'department': emp.department or 'N/A',
                        'joining_date': emp.joining_date.strftime('%d %b %Y') if emp.joining_date else 'N/A',
                        'status': emp.status
                    } for emp in employees]
                finally:
                    db.close()

                table = ui.table(columns=columns, rows=rows, row_key='employee_id').classes('w-full glass-card p-4').props('flat hide-bottom')
                
                # Custom employee_id column renderer
                table.add_slot('body-cell-employee_id', '''
                    <q-td :props="props">
                        <span class="font-mono text-xs font-bold text-primary bg-teal-50 px-2 py-1 rounded border border-teal-100">
                            {{ props.value }}
                        </span>
                    </q-td>
                ''')

                # Custom phone number column renderer
                table.add_slot('body-cell-phone_number', '''
                    <q-td :props="props">
                        <div class="row items-center no-wrap">
                            <q-icon name="phone" class="text-teal-600 q-mr-xs" size="14px" />
                            <span>{{ props.value }}</span>
                        </div>
                    </q-td>
                ''')

                # Custom role column renderer
                table.add_slot('body-cell-role', '''
                    <q-td :props="props" class="text-center">
                        <q-badge :color="props.value === 'admin' ? 'indigo-10' : 'blue-grey-6'" class="q-py-xs q-px-sm font-semibold">
                            <q-icon :name="props.value === 'admin' ? 'security' : 'person'" class="q-mr-xs" size="14px" />
                            {{ props.value.toUpperCase() }}
                        </q-badge>
                    </q-td>
                ''')

                # Custom department column renderer
                table.add_slot('body-cell-department', '''
                    <q-td :props="props">
                        <q-badge outline color="teal-8" class="q-py-xs q-px-sm font-semibold">
                            <q-icon name="lan" class="q-mr-xs" size="14px" />
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                ''')

                # Custom joining_date column renderer
                table.add_slot('body-cell-joining_date', '''
                    <q-td :props="props" class="text-center">
                        <div class="row items-center justify-center no-wrap">
                            <q-icon name="calendar_today" class="text-teal-600 q-mr-xs" size="14px" />
                            <span>{{ props.value }}</span>
                        </div>
                    </q-td>
                ''')

                # Custom status column renderer using slot APIs
                table.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <span :class="props.value === 'active' ? 'badge-status badge-completed' : 'badge-status badge-blocked'">
                            {{ props.value }}
                        </span>
                    </q-td>
                ''')
        
                # Custom action column renderer
                table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat round dense color="primary" icon="edit" @click="$parent.$emit('edit_emp', props.row)">
                            <q-tooltip class="bg-indigo text-white">Edit Employee</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense color="negative" icon="delete" @click="$parent.$emit('delete_emp', props.row)">
                            <q-tooltip class="bg-red text-white">Delete Employee</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')

                # Listen to Table Events
                def handle_toggle(emp_id):
                    t_db = SessionLocal()
                    try:
                        ok, msg = toggle_employee_status(t_db, app.storage.user.get('employee_id'), emp_id)
                        if ok:
                            ui.notify(msg, type='positive')
                            run_search() # Reload table
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        t_db.close()
                        
                table.on('toggle_emp', lambda msg: handle_toggle(msg.args))

            # ── Panel 2: Pending Requests ────────────────────────────────
            with ui.tab_panel('pending').classes('p-0 bg-transparent'):
                pending_container = ui.element('div').classes('w-full')
                
                def render_pending():
                    pending_container.clear()
                    db_p = SessionLocal()
                    try:
                        employees_pending = get_all_registration_requests(db_p, status_filter='pending')
                    finally:
                        db_p.close()
                        
                    with pending_container:
                        if not employees_pending:
                            with ui.element('div').classes('glass-card p-12 text-center w-full'):
                                ui.element('i').classes('ri-inbox-line text-6xl text-gray-300 mb-4')
                                ui.label('No pending requests found.').classes('text-gray-400 text-lg')
                            return
                            
                        with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 w-full'):
                            for emp in employees_pending:
                                _render_request_card(emp, 'pending')
                
                render_pending()

            # ── Panel 3: Rejected Requests ───────────────────────────────
            with ui.tab_panel('rejected').classes('p-0 bg-transparent'):
                rejected_container = ui.element('div').classes('w-full')
                
                def render_rejected():
                    rejected_container.clear()
                    db_r = SessionLocal()
                    try:
                        employees_rejected = get_all_registration_requests(db_r, status_filter='rejected')
                    finally:
                        db_r.close()
                        
                    with rejected_container:
                        if not employees_rejected:
                            with ui.element('div').classes('glass-card p-12 text-center w-full'):
                                ui.element('i').classes('ri-inbox-line text-6xl text-gray-300 mb-4')
                                ui.label('No rejected requests found.').classes('text-gray-400 text-lg')
                            return
                            
                        with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 w-full'):
                            for emp in employees_rejected:
                                _render_request_card(emp, 'rejected')
                                
                render_rejected()

        # ADD DIALOG MODAL
        def open_add_modal():
            with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                ui.label('Add Employee').classes('text-xl font-bold mb-4')
                
                e_id = ui.input('Employee ID (e.g. EMP101)').classes('w-full mb-3').props('outlined color=primary')
                e_name = ui.input('Full Name').classes('w-full mb-3').props('outlined color=primary')
                e_phone = ui.input('Phone Number').classes('w-full mb-3').props('outlined color=primary')
                e_dept = ui.select({
                    '': 'Select department',
                    'AI / ML': 'AI / ML',
                    'IoT': 'IoT',
                    'Robotics': 'Robotics',
                    'AR / VR': 'AR / VR',
                    'Others': 'Others'
                }, value='').classes('w-full mb-3').props('outlined')
                e_dept_other = ui.input('Specify Department').classes('w-full mb-3').props('outlined color=primary').bind_visibility_from(e_dept, 'value', value='Others')
                e_role = ui.select({'employee': 'Employee', 'admin': 'Administrator'}, value='employee').classes('w-full mb-3').props('outlined')
                e_join = ui.input('Joining Date (YYYY-MM-DD)', value=date.today().strftime('%Y-%m-%d')).classes('w-full mb-3').props('outlined color=primary')
                e_password = ui.input('Password').classes('w-full mb-3').props('outlined color=primary type=password')
                e_confirm_password = ui.input('Confirm Password').classes('w-full mb-4').props('outlined color=primary type=password')

                def save():
                    if not e_id.value or not e_name.value or not e_phone.value or not e_password.value or not e_confirm_password.value:
                        ui.notify('Please fill all required fields including Password', type='warning')
                        return
                    if e_password.value != e_confirm_password.value:
                        ui.notify('Passwords do not match', type='negative')
                        return
                        
                    # Parse Date
                    try:
                        join_date = datetime.strptime(e_join.value, '%Y-%m-%d').date()
                    except:
                        join_date = date.today()
                        
                    s_db = SessionLocal()
                    try:
                        dept_val = e_dept_other.value.strip() if e_dept.value == 'Others' else e_dept.value
                        # Setting initial password same as ID as default
                        ok, msg = add_employee(
                            db=s_db,
                            creator_id=app.storage.user.get('employee_id'),
                            employee_id=e_id.value,
                            employee_name=e_name.value,
                            phone_number=e_phone.value,
                            password=e_password.value if e_password.value else e_id.value,
                            role=e_role.value,
                            department=dept_val,
                            joining_date=join_date
                        )
                        if ok:
                            ui.notify(msg, type='positive')
                            dialog.close()
                            run_search()
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        s_db.close()

                with ui.row().classes('w-full justify-end mt-4 gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                    ui.button('Create Account', on_click=save).classes('btn-neon')
            dialog.open()

        # EDIT DIALOG MODAL
        def open_edit_modal(row_data):
            dept_predefined = ['AI / ML', 'IoT', 'Robotics', 'AR / VR']
            current_dept = row_data['department'] if row_data['department'] != 'N/A' else ''
            
            if current_dept in dept_predefined:
                dept_select_val = current_dept
                dept_other_val = ''
            elif current_dept == '':
                dept_select_val = ''
                dept_other_val = ''
            else:
                dept_select_val = 'Others'
                dept_other_val = current_dept

            with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                ui.label(f"Edit Employee: {row_data['employee_id']}").classes('text-xl font-bold mb-4')
                
                e_name = ui.input('Full Name', value=row_data['employee_name']).classes('w-full mb-3').props('outlined color=primary')
                e_phone = ui.input('Phone Number', value=row_data['phone_number']).classes('w-full mb-3').props('outlined color=primary')
                e_dept = ui.select({
                    '': 'Select department',
                    'AI / ML': 'AI / ML',
                    'IoT': 'IoT',
                    'Robotics': 'Robotics',
                    'AR / VR': 'AR / VR',
                    'Others': 'Others'
                }, value=dept_select_val).classes('w-full mb-3').props('outlined')
                e_dept_other = ui.input('Specify Department', value=dept_other_val).classes('w-full mb-3').props('outlined color=primary').bind_visibility_from(e_dept, 'value', value='Others')
                e_status = ui.select({'active': 'Active', 'inactive': 'Inactive'}, value=row_data['status']).classes('w-full mb-4').props('outlined')

                def save():
                    if not e_name.value or not e_phone.value:
                        ui.notify('Please fill all required fields', type='warning')
                        return
                        
                    s_db = SessionLocal()
                    try:
                        dept_val = e_dept_other.value.strip() if e_dept.value == 'Others' else e_dept.value
                        ok, msg = update_employee(
                            db=s_db,
                            updater_id=app.storage.user.get('employee_id'),
                            employee_id=row_data['employee_id'],
                            department=dept_val,
                            employee_name=e_name.value,
                            phone_number=e_phone.value,
                            status=e_status.value
                        )
                        if ok:
                            ui.notify(msg, type='positive')
                            dialog.close()
                            run_search()
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        s_db.close()

                with ui.row().classes('w-full justify-end mt-4 gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                    ui.button('Update Account', on_click=save).classes('btn-neon')
            dialog.open()
            
        table.on('edit_emp', lambda msg: open_edit_modal(msg.args))

        # RESET PASSWORD DIALOG
        def open_reset_pwd_modal(emp_id):
            with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                ui.label(f"Reset Password: {emp_id}").classes('text-xl font-bold mb-2')
                ui.label('Provide a new password (min. 6 characters)').classes('text-gray-500 text-xs mb-4')
                
                new_pwd = ui.input('New Password', password=True).classes('w-full mb-4').props('outlined color=primary')

                def save():
                    if not new_pwd.value or len(new_pwd.value) < 6:
                        ui.notify('Password must be at least 6 characters long', type='warning')
                        return
                        
                    s_db = SessionLocal()
                    try:
                        ok, msg = reset_employee_password(
                            db=s_db,
                            admin_id=app.storage.user.get('employee_id'),
                            employee_id=emp_id,
                            new_password=new_pwd.value
                        )
                        if ok:
                            ui.notify(msg, type='positive')
                            dialog.close()
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        s_db.close()

                with ui.row().classes('w-full justify-end mt-4 gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                    ui.button('Save Password', on_click=save).classes('btn-neon')
            dialog.open()
            
        table.on('reset_pwd', lambda msg: open_reset_pwd_modal(msg.args))

        # DELETE EMPLOYEE DIALOG
        def open_delete_modal(row_data):
            emp_id = row_data['employee_id']
            emp_name = row_data['employee_name']

            with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                ui.label('Delete Employee').classes('text-xl font-bold mb-2')
                ui.label(f"Delete {emp_name} ({emp_id})? This will remove the employee account and related task/activity records.").classes('text-gray-600 text-sm mb-4')

                def confirm_delete():
                    d_db = SessionLocal()
                    try:
                        ok, msg = delete_employee(
                            db=d_db,
                            admin_id=app.storage.user.get('employee_id'),
                            employee_id=emp_id
                        )
                        if ok:
                            ui.notify(msg, type='positive')
                            dialog.close()
                            run_search()
                        else:
                            ui.notify(msg, type='negative')
                    finally:
                        d_db.close()

                with ui.row().classes('w-full justify-end mt-4 gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                    ui.button('Delete Employee', icon='delete', on_click=confirm_delete).props('color=negative')
            dialog.open()

        table.on('delete_emp', lambda msg: open_delete_modal(msg.args))


@ui.page('/admin/tasks')
def view_all_tasks():
    # Authenticate and authorize admin
    if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
        ui.navigate.to('/login')
        return

    db = SessionLocal()
    try:
        # Query all employees for filter dropdown
        employees = get_all_employees(db)
        emp_choices = {'All': 'All Employees'}
        for e in employees:
            emp_choices[e.employee_id] = f"{e.employee_name} ({e.employee_id})"
            
        # Fetch all tasks initially
        tasks = db.query(Task, Employee).join(Employee, Task.employee_id == Employee.employee_id)\
            .order_by(Task.created_date.desc(), Task.created_time.desc()).all()
            
        rows = []
        for t, e in tasks:
            rows.append({
                'task_id': t.task_id,
                'date_time': f"{t.created_date.strftime('%Y-%m-%d')} {t.created_time.strftime('%I:%M %p')}",
                'employee_id': e.employee_id,
                'employee_name': e.employee_name,
                'department': e.department or 'N/A',
                'title': t.title,
                'description': t.description or 'No description.',
                'status': t.status
            })
    finally:
        db.close()

    with render_layout('/admin/tasks'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-8'):
            with ui.element('div'):
                ui.label('Employee Task Registry').classes('text-3xl font-bold tracking-tight')
                ui.label('Monitor and search daily task logs submitted by staff').classes('text-gray-500 text-sm')

        # Filter Controls
        with ui.element('div').classes('glass-card p-6 w-full mb-6'):
            with ui.grid().classes('grid-cols-1 md:grid-cols-5 gap-4 items-center'):
                search_input = ui.input(placeholder='Search tasks or name...').classes('w-full').props('outlined dense color=primary')
                emp_select = ui.select(emp_choices, value='All').classes('w-full').props('outlined dense')
                status_select = ui.select({
                    'All': 'All Statuses',
                    'Pending': 'Pending',
                    'Work In Progress': 'In Progress',
                    'Completed': 'Completed',
                    'Blocked': 'Blocked',
                    'On Hold': 'On Hold'
                }, value='All').classes('w-full').props('outlined dense')
                
                start_date = ui.input('Start Date (YYYY-MM-DD)').classes('w-full').props('outlined dense color=primary')
                end_date = ui.input('End Date (YYYY-MM-DD)').classes('w-full').props('outlined dense color=primary')

            def run_filter():
                f_db = SessionLocal()
                try:
                    from sqlalchemy import or_
                    query = f_db.query(Task, Employee).join(Employee, Task.employee_id == Employee.employee_id)
                    
                    # Text search
                    q = search_input.value
                    if q:
                        pattern = f"%{q}%"
                        query = query.filter(
                            or_(
                                Task.title.like(pattern),
                                Task.description.like(pattern),
                                Employee.employee_name.like(pattern),
                                Employee.employee_id.like(pattern)
                            )
                        )
                        
                    # Employee ID filter
                    s_emp = emp_select.value
                    if s_emp and s_emp != 'All':
                        query = query.filter(Task.employee_id == s_emp)
                        
                    # Status filter
                    s_status = status_select.value
                    if s_status and s_status != 'All':
                        query = query.filter(Task.status == s_status)
                        
                    # Dates
                    if start_date.value:
                        try:
                            sd = datetime.strptime(start_date.value, '%Y-%m-%d').date()
                            query = query.filter(Task.created_date >= sd)
                        except:
                            pass
                    if end_date.value:
                        try:
                            ed = datetime.strptime(end_date.value, '%Y-%m-%d').date()
                            query = query.filter(Task.created_date <= ed)
                        except:
                            pass
                            
                    res = query.order_by(Task.created_date.desc(), Task.created_time.desc()).all()
                    table.rows = [{
                        'task_id': t.task_id,
                        'date_time': f"{t.created_date.strftime('%Y-%m-%d')} {t.created_time.strftime('%I:%M %p')}",
                        'employee_id': e.employee_id,
                        'employee_name': e.employee_name,
                        'department': e.department or 'N/A',
                        'title': t.title,
                        'description': t.description or 'No description.',
                        'status': t.status
                    } for t, e in res]
                finally:
                    f_db.close()

            # Bind events for automatic, reactive updates
            search_input.on('change', run_filter)
            emp_select.on('change', run_filter)
            status_select.on('change', run_filter)
            start_date.on('change', run_filter)
            end_date.on('change', run_filter)

        # Columns definition for table
        columns = [
            {'name': 'date_time', 'label': 'Date & Time', 'field': 'date_time', 'align': 'center', 'sortable': True},
            {'name': 'employee', 'label': 'Employee', 'field': 'employee_name', 'align': 'left', 'sortable': True},
            {'name': 'department', 'label': 'Department', 'field': 'department', 'align': 'left', 'sortable': True},
            {'name': 'task_details', 'label': 'Task Title & Description', 'field': 'title', 'align': 'left'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True}
        ]

        # Render Table
        table = ui.table(columns=columns, rows=rows, row_key='task_id').classes('w-full glass-card p-4').props('flat')
        
        # Custom slot for Employee column
        table.add_slot('body-cell-employee', '''
            <q-td :props="props">
                <div class="font-bold text-slate-900">{{ props.row.employee_name }}</div>
                <div class="text-xs text-gray-500">ID: {{ props.row.employee_id }}</div>
            </q-td>
        ''')

        # Custom slot for Task Details
        table.add_slot('body-cell-task_details', '''
            <q-td :props="props">
                <div class="font-bold text-slate-900">{{ props.row.title }}</div>
                <div class="text-xs text-gray-600 text-wrap" style="max-width: 450px;">{{ props.row.description }}</div>
            </q-td>
        ''')

        # Custom slot for Status column
        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <span :class="'badge-status badge-' + (props.value === 'Completed' ? 'completed' : props.value === 'Work In Progress' ? 'wip' : props.value === 'Blocked' ? 'blocked' : props.value === 'On Hold' ? 'hold' : 'pending')">
                    {{ props.value }}
                </span>
            </q-td>
        ''')



