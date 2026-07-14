from nicegui import app, ui
from models import SessionLocal
from models.employee import Employee
from models.task import Task
from models.activity_log import ActivityLog
from services.employee_service import (
    get_all_employees, search_employees, add_employee, 
    update_employee, toggle_employee_status, reset_employee_password
)
from services.auth_service import log_activity
from pages.layout import render_layout
from datetime import date, datetime, timedelta
from sqlalchemy import func
import os

def init_admin_routes():
    
    @ui.page('/admin')
    def admin_dashboard():
        # Authenticate and authorize admin role
        if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
            ui.navigate.to('/login')
            return
            
        db = SessionLocal()
        try:
            today = date.today()
            
            # 1. Gather Statistics
            total_employees = db.query(Employee).count()
            inactive_employees = db.query(Employee).filter(Employee.status == 'inactive').count()
            
            today_tasks = db.query(Task).filter(Task.created_date == today).all()
            today_count = len(today_tasks)
            
            completed_today = sum(1 for t in today_tasks if t.status == 'Completed')
            wip_today = sum(1 for t in today_tasks if t.status == 'Work In Progress')
            pending_today = sum(1 for t in today_tasks if t.status == 'Pending')
            blocked_today = sum(1 for t in today_tasks if t.status == 'Blocked')
            on_hold_today = sum(1 for t in today_tasks if t.status == 'On Hold')
            
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
        with render_layout('/admin'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label('Admin Dashboard').classes('text-3xl font-bold tracking-tight')
                    ui.label('Overview of company task progress and employee status').classes('text-gray-500 text-sm')
                
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
                with ui.element('div').classes('glass-card p-6 metric-card'):
                    with ui.row().classes('justify-between items-center'):
                        ui.label('Total Employees').classes('text-gray-500 text-sm font-semibold')
                        ui.element('i').classes('ri-group-line text-primary text-2xl')
                    ui.label(str(total_employees)).classes('text-4xl font-bold mt-2')
                    ui.label(f"{inactive_employees} inactive accounts").classes('text-gray-500 text-xs mt-1')

                # Card 2: Today's Tasks
                with ui.element('div').classes('glass-card p-6 metric-card'):
                    with ui.row().classes('justify-between items-center'):
                        ui.label('Today\'s Submissions').classes('text-gray-500 text-sm font-semibold')
                        ui.element('i').classes('ri-file-list-3-line text-primary text-2xl')
                    ui.label(str(today_count)).classes('text-4xl font-bold mt-2')
                    ui.label(f"{pending_today} pending | {wip_today} in progress").classes('text-gray-500 text-xs mt-1')

                # Card 3: Completion Rate
                with ui.element('div').classes('glass-card p-6 metric-card'):
                    with ui.row().classes('justify-between items-center'):
                        ui.label('Completion Rate').classes('text-gray-500 text-sm font-semibold')
                        ui.element('i').classes('ri-pie-chart-line text-emerald-600 text-2xl')
                    ui.label(f"{completion_rate}%").classes('text-emerald-600 text-4xl font-bold mt-2')
                    ui.label(f"{completed_today} completed tasks today").classes('text-gray-500 text-xs mt-1')

                # Card 4: Action Blockers
                with ui.element('div').classes('glass-card p-6 metric-card'):
                    with ui.row().classes('justify-between items-center'):
                        ui.label('Blocked & Hold').classes('text-gray-500 text-sm font-semibold')
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
                        'legend': {'orient': 'horizontal', 'bottom': '0', 'textStyle': {'color': '#94A3B8'}},
                        'series': [{
                            'name': 'Tasks',
                            'type': 'pie',
                            'radius': ['40%', '70%'],
                            'avoidLabelOverlap': False,
                            'itemStyle': {'borderRadius': 6, 'borderColor': '#111827', 'borderWidth': 2},
                            'label': {'show': False},
                            'emphasis': {'label': {'show': True, 'fontSize': '14', 'fontWeight': 'bold', 'color': '#FFFFFF'}},
                            'data': [
                                {'value': completed_today, 'name': 'Completed', 'itemStyle': {'color': '#20c997'}},
                                {'value': wip_today, 'name': 'In Progress', 'itemStyle': {'color': '#8b5cf6'}},
                                {'value': pending_today, 'name': 'Pending', 'itemStyle': {'color': '#3b82f6'}},
                                {'value': blocked_today, 'name': 'Blocked', 'itemStyle': {'color': '#ef4444'}},
                                {'value': on_hold_today, 'name': 'On Hold', 'itemStyle': {'color': '#f59e0b'}}
                            ]
                        }]
                    }
                    ui.echart(options=pie_options).classes('w-full h-64')

            # 4. Recent Task Submissions
            with ui.element('div').classes('glass-card p-6 w-full'):
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
                                    ui.label(f"{task.created_date.strftime('%Y-%m-%d')} {task.created_time.strftime('%I:%M %p')}")
                                with ui.element('td').classes('p-3 font-semibold'):
                                    ui.label(f"{emp.employee_name} ({emp.employee_id})")
                                with ui.element('td').classes('p-3 text-gray-700'):
                                    ui.label(task.title)
                                with ui.element('td').classes('p-3'):
                                    badge_class = 'completed' if task.status == 'Completed' else \
                                                  'wip' if task.status == 'Work In Progress' else \
                                                  'blocked' if task.status == 'Blocked' else \
                                                  'hold' if task.status == 'On Hold' else 'pending'
                                    ui.html(f'<span class="badge-status badge-{badge_class}">{task.status}</span>')


    @ui.page('/admin/employees')
    def employee_management():
        # Authenticate and authorize admin
        if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
            ui.navigate.to('/login')
            return

        db = SessionLocal()
        try:
            employees = get_all_employees(db)
            rows = []
            for emp in employees:
                rows.append({
                    'employee_id': emp.employee_id,
                    'employee_name': emp.employee_name,
                    'phone_number': emp.phone_number,
                    'role': emp.role,
                    'department': emp.department or 'N/A',
                    'joining_date': emp.joining_date.strftime('%Y-%m-%d'),
                    'status': emp.status
                })
        finally:
            db.close()

        # Renders the main wrapping page layout
        with render_layout('/admin/employees'):
            
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label('Employee Registry').classes('text-3xl font-bold tracking-tight')
                    ui.label('Manage staff credentials, department allocations, and access permissions').classes('text-gray-500 text-sm')
                
                ui.button('Add New Employee', icon='person_add', on_click=lambda: open_add_modal()).classes('btn-neon')

            # Search bar
            with ui.row().classes('w-full mb-6 items-center'):
                search_input = ui.input(placeholder='Search by ID, Name, Phone or Department...').classes('w-96').props('outlined dense color=primary')
                
                def run_search():
                    q = search_input.value
                    s_db = SessionLocal()
                    try:
                        res = search_employees(s_db, q)
                        table.rows = [{
                            'employee_id': emp.employee_id,
                            'employee_name': emp.employee_name,
                            'phone_number': emp.phone_number,
                            'role': emp.role,
                            'department': emp.department or 'N/A',
                            'joining_date': emp.joining_date.strftime('%Y-%m-%d'),
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

            table = ui.table(columns=columns, rows=rows, row_key='employee_id').classes('w-full glass-card p-4').props('flat hide-bottom')
            
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
                    <q-btn flat round dense :color="props.row.status === 'active' ? 'warning' : 'positive'" icon="power_settings_new" @click="$parent.$emit('toggle_emp', props.row.employee_id)">
                        <q-tooltip class="bg-amber text-white">Toggle Active/Inactive</q-tooltip>
                    </q-btn>
                    <q-btn flat round dense color="secondary" icon="vpn_key" @click="$parent.$emit('reset_pwd', props.row.employee_id)">
                        <q-tooltip class="bg-purple text-white">Reset Password</q-tooltip>
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

            # ADD DIALOG MODAL
            def open_add_modal():
                with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                    ui.label('Add Employee').classes('text-xl font-bold mb-4')
                    
                    e_id = ui.input('Employee ID (e.g. EMP101)').classes('w-full mb-3').props('outlined color=primary')
                    e_name = ui.input('Full Name').classes('w-full mb-3').props('outlined color=primary')
                    e_phone = ui.input('Phone Number').classes('w-full mb-3').props('outlined color=primary')
                    e_dept = ui.input('Department (Optional)').classes('w-full mb-3').props('outlined color=primary')
                    e_role = ui.select({'employee': 'Employee', 'admin': 'Administrator'}, value='employee').classes('w-full mb-3').props('outlined')
                    e_join = ui.input('Joining Date (YYYY-MM-DD)', value=date.today().strftime('%Y-%m-%d')).classes('w-full mb-4').props('outlined color=primary')
                    
                    # Password is automatically generated as ID + 'Pass'
                    ui.label("Temporary Password: Set same as Employee ID (forces login)").classes('text-gray-500 text-xs mb-4')

                    def save():
                        if not e_id.value or not e_name.value or not e_phone.value:
                            ui.notify('Please fill all required fields', type='warning')
                            return
                            
                        # Parse Date
                        try:
                            join_date = datetime.strptime(e_join.value, '%Y-%m-%d').date()
                        except:
                            join_date = date.today()
                            
                        s_db = SessionLocal()
                        try:
                            # Setting initial password same as ID as default
                            ok, msg = add_employee(
                                db=s_db,
                                creator_id=app.storage.user.get('employee_id'),
                                employee_id=e_id.value,
                                employee_name=e_name.value,
                                phone_number=e_phone.value,
                                password=e_id.value,
                                role=e_role.value,
                                department=e_dept.value,
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
                with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('glass-card p-6 w-full'):
                    ui.label(f"Edit Employee: {row_data['employee_id']}").classes('text-xl font-bold mb-4')
                    
                    e_name = ui.input('Full Name', value=row_data['employee_name']).classes('w-full mb-3').props('outlined color=primary')
                    e_phone = ui.input('Phone Number', value=row_data['phone_number']).classes('w-full mb-3').props('outlined color=primary')
                    e_dept = ui.input('Department', value=row_data['department'] if row_data['department'] != 'N/A' else '').classes('w-full mb-3').props('outlined color=primary')
                    e_status = ui.select({'active': 'Active', 'inactive': 'Inactive'}, value=row_data['status']).classes('w-full mb-4').props('outlined')

                    def save():
                        if not e_name.value or not e_phone.value:
                            ui.notify('Please fill all required fields', type='warning')
                            return
                            
                        s_db = SessionLocal()
                        try:
                            ok, msg = update_employee(
                                db=s_db,
                                updater_id=app.storage.user.get('employee_id'),
                                employee_id=row_data['employee_id'],
                                employee_name=e_name.value,
                                phone_number=e_phone.value,
                                department=e_dept.value,
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
