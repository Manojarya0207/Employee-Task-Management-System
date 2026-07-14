from nicegui import app, ui
from models import SessionLocal
from models.task import Task
from models.employee import Employee
from services.task_service import (
    get_employee_tasks, add_task, update_task, 
    get_filtered_tasks, get_tasks_by_period, get_calendar_events
)
from services.auth_service import change_user_password
from services.employee_service import get_employee_by_id
from pages.layout import render_layout
from datetime import date, datetime, timedelta
import json

def init_employee_routes():

    @ui.page('/employee')
    def employee_dashboard():
        # Authenticate employee
        if not app.storage.user.get('authenticated', False):
            ui.navigate.to('/login')
            return
            
        emp_id = app.storage.user.get('employee_id')
        
        db = SessionLocal()
        try:
            today = date.today()
            
            # Fetch employee profile details
            emp_profile = get_employee_by_id(db, emp_id)
            
            # Fetch today's tasks
            today_tasks = db.query(Task).filter(
                Task.employee_id == emp_id,
                Task.created_date == today
            ).order_by(Task.created_time.desc()).all()
            
            today_count = len(today_tasks)
            completed_count = sum(1 for t in today_tasks if t.status == 'Completed')
            wip_count = sum(1 for t in today_tasks if t.status == 'Work In Progress')
            pending_count = sum(1 for t in today_tasks if t.status == 'Pending')
            
            # This week's tasks count
            start_of_week = today - timedelta(days=today.weekday())
            week_tasks_count = db.query(Task).filter(
                Task.employee_id == emp_id,
                Task.created_date >= start_of_week
            ).count()
            
            # Check reminder requirement (If past 6:00 PM and no submissions today)
            show_reminder = False
            current_hour = datetime.now().hour
            if today_count == 0 and current_hour >= 18:
                show_reminder = True

            rows = []
            for t in today_tasks:
                rows.append({
                    'task_id': t.task_id,
                    'title': t.title,
                    'description': t.description or 'No description provided.',
                    'status': t.status,
                    'time': t.created_time.strftime('%I:%M %p'),
                    'last_modified': t.last_modified.strftime('%I:%M %p')
                })
        finally:
            db.close()

        # Render layout
        with render_layout('/employee'):
            # Reminder banner
            if show_reminder:
                with ui.element('div').classes('w-full mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between'):
                    with ui.row().classes('items-center gap-3'):
                        ui.element('i').classes('ri-error-warning-fill text-red-500 text-2xl')
                        with ui.element('div'):
                            ui.label('Daily Submission Reminder!').classes('text-red-900 font-bold')
                            ui.label('You haven\'t logged any work items for today yet. Please submit your updates.').classes('text-red-700 text-xs')
                    ui.button('Submit Now', icon='add', on_click=lambda: open_add_task_modal()).classes('bg-red-600 hover:bg-red-700 text-white rounded-lg')

            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label(f"Welcome, {emp_profile.employee_name}").classes('text-3xl font-bold tracking-tight')
                    ui.label('Log your updates and track daily goals').classes('text-gray-500 text-sm')
                
                ui.button('Add Daily Task', icon='add_task', on_click=lambda: open_add_task_modal()).classes('btn-neon')

            # Metric grid
            with ui.grid().classes('grid-cols-1 md:grid-cols-4 gap-6 mb-8 w-full'):
                with ui.element('div').classes('glass-card p-6 metric-card'):
                    ui.label('Logged Today').classes('text-gray-500 text-sm font-semibold')
                    ui.label(str(today_count)).classes('text-4xl font-bold mt-2')
                    ui.label('Tasks created today').classes('text-gray-500 text-xs mt-1')

                with ui.element('div').classes('glass-card p-6 metric-card'):
                    ui.label('Completed').classes('text-gray-500 text-sm font-semibold')
                    ui.label(str(completed_count)).classes('text-emerald-600 text-4xl font-bold mt-2')
                    ui.label('Goals finished').classes('text-gray-500 text-xs mt-1')

                with ui.element('div').classes('glass-card p-6 metric-card'):
                    ui.label('Pending / WIP').classes('text-gray-500 text-sm font-semibold')
                    ui.label(str(pending_count + wip_count)).classes('text-indigo-600 text-4xl font-bold mt-2')
                    ui.label('Work items in progress').classes('text-gray-500 text-xs mt-1')

                with ui.element('div').classes('glass-card p-6 metric-card'):
                    ui.label('This Week Tasks').classes('text-gray-500 text-sm font-semibold')
                    ui.label(str(week_tasks_count)).classes('text-4xl font-bold mt-2')
                    ui.label('Tasks since Monday').classes('text-gray-500 text-xs mt-1')

            # Today's Task Table
            ui.label('Today\'s Task Updates').classes('text-xl font-bold mb-4')
            
            columns = [
                {'name': 'time', 'label': 'Logged Time', 'field': 'time', 'align': 'center'},
                {'name': 'title', 'label': 'Task Title', 'field': 'title', 'align': 'left', 'required': True},
                {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                {'name': 'last_modified', 'label': 'Last Modified', 'field': 'last_modified', 'align': 'center'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ]

            if not rows:
                with ui.element('div').classes('w-full glass-card p-12 flex flex-col items-center justify-center text-center'):
                    ui.element('i').classes('ri-file-shred-line text-gray-500 text-5xl mb-4')
                    ui.label('No Tasks Submitted Today').classes('font-semibold text-lg')
                    ui.label('Click "Add Daily Task" to log your updates for today.').classes('text-gray-500 text-sm mt-1')
            else:
                table = ui.table(columns=columns, rows=rows, row_key='task_id').classes('w-full glass-card p-4').props('flat hide-bottom')
                
                # Render custom status chip
                table.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <span :class="'badge-status badge-' + (props.value === 'Completed' ? 'completed' : props.value === 'Work In Progress' ? 'wip' : props.value === 'Blocked' ? 'blocked' : props.value === 'On Hold' ? 'hold' : 'pending')">
                            {{ props.value }}
                        </span>
                    </q-td>
                ''')

                # Action buttons (Edit enabled because it is today's task table)
                table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat round dense color="primary" icon="edit" @click="$parent.$emit('edit_task', props.row)">
                            <q-tooltip class="bg-indigo text-white">Edit Task</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')

                def reload_page():
                    ui.navigate.to('/employee')

                # Edit Task event handler
                def handle_edit_task_event(row_data):
                    open_edit_task_modal(row_data, callback=reload_page)
                    
                table.on('edit_task', lambda msg: handle_edit_task_event(msg.args))

            # ADD TASK MODAL
            def open_add_task_modal():
                with ui.dialog().classes('w-full max-w-lg') as dialog, ui.card().classes('glass-card p-6 w-full'):
                    ui.label('Add Task Update').classes('text-xl font-bold mb-4')
                    
                    t_title = ui.input('Task Title').classes('w-full mb-3').props('outlined color=primary')
                    t_desc = ui.textarea('Task Description').classes('w-full mb-3').props('outlined color=primary')
                    t_status = ui.select({
                        'Pending': 'Pending',
                        'Work In Progress': 'Work In Progress',
                        'Completed': 'Completed',
                        'Blocked': 'Blocked',
                        'On Hold': 'On Hold'
                    }, value='Pending').classes('w-full mb-6').props('outlined')

                    def save():
                        if not t_title.value:
                            ui.notify('Task Title is required', type='warning')
                            return
                            
                        s_db = SessionLocal()
                        try:
                            ok, msg = add_task(
                                db=s_db,
                                employee_id=emp_id,
                                title=t_title.value,
                                description=t_desc.value,
                                status=t_status.value
                            )
                            if ok:
                                ui.notify(msg, type='positive')
                                dialog.close()
                                ui.navigate.to('/employee')
                            else:
                                ui.notify(msg, type='negative')
                        finally:
                            s_db.close()

                    with ui.row().classes('w-full justify-end mt-4 gap-2'):
                        ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                        ui.button('Submit Task', on_click=save).classes('btn-neon')
                dialog.open()

            # EDIT TASK MODAL
            def open_edit_task_modal(row_data, callback=None):
                with ui.dialog().classes('w-full max-w-lg') as dialog, ui.card().classes('glass-card p-6 w-full'):
                    ui.label('Edit Task Update').classes('text-xl font-bold mb-4')
                    
                    t_title = ui.input('Task Title', value=row_data['title']).classes('w-full mb-3').props('outlined color=primary')
                    t_desc = ui.textarea('Task Description', value=row_data['description']).classes('w-full mb-3').props('outlined color=primary')
                    t_status = ui.select({
                        'Pending': 'Pending',
                        'Work In Progress': 'Work In Progress',
                        'Completed': 'Completed',
                        'Blocked': 'Blocked',
                        'On Hold': 'On Hold'
                    }, value=row_data['status']).classes('w-full mb-6').props('outlined')

                    def save():
                        if not t_title.value:
                            ui.notify('Task Title is required', type='warning')
                            return
                            
                        s_db = SessionLocal()
                        try:
                            ok, msg = update_task(
                                db=s_db,
                                employee_id=emp_id,
                                task_id=row_data['task_id'],
                                title=t_title.value,
                                description=t_desc.value,
                                status=t_status.value
                            )
                            if ok:
                                ui.notify(msg, type='positive')
                                dialog.close()
                                if callback:
                                    callback()
                            else:
                                ui.notify(msg, type='negative')
                        finally:
                            s_db.close()

                    with ui.row().classes('w-full justify-end mt-4 gap-2'):
                        ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                        ui.button('Update Task', on_click=save).classes('btn-neon')
                dialog.open()


    @ui.page('/employee/history')
    def task_history():
        # Authenticate employee
        if not app.storage.user.get('authenticated', False):
            ui.navigate.to('/login')
            return
            
        emp_id = app.storage.user.get('employee_id')
        
        db = SessionLocal()
        try:
            tasks = get_employee_tasks(db, emp_id)
            events = get_calendar_events(db, emp_id)
            
            rows = []
            for t in tasks:
                rows.append({
                    'task_id': t.task_id,
                    'date': t.created_date.strftime('%Y-%m-%d'),
                    'time': t.created_time.strftime('%I:%M %p'),
                    'title': t.title,
                    'description': t.description or 'No description.',
                    'status': t.status,
                    'is_today': t.created_date == date.today()
                })
        finally:
            db.close()

        with render_layout('/employee/history'):
            
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label('Tasks & Submission History').classes('text-3xl font-bold tracking-tight')
                    ui.label('Search past reports, filter results, and view visual calendar tracking').classes('text-gray-500 text-sm')

            # Layout: Tab selector between List View and Calendar View
            with ui.tabs().classes('w-full mb-6 border-b border-slate-200') as tabs:
                list_tab = ui.tab('List View', icon='list')
                calendar_tab = ui.tab('Calendar Grid', icon='calendar_month')
                
            with ui.tab_panels(tabs, value=list_tab).classes('w-full bg-transparent'):
                
                # PANEL 1: LIST VIEW
                with ui.tab_panel(list_tab).classes('p-0 bg-transparent'):
                    # Filters
                    with ui.row().classes('w-full mb-6 items-center justify-between gap-4'):
                        with ui.row().classes('items-center gap-3'):
                            period_filter = ui.select({
                                'all': 'All History',
                                'today': 'Today Only',
                                'yesterday': 'Yesterday',
                                'last_week': 'Last 7 Days',
                                'last_month': 'Last 30 Days'
                            }, value='all').classes('w-48').props('outlined dense')
                            
                            status_filter = ui.select({
                                'All': 'All Statuses',
                                'Pending': 'Pending',
                                'Work In Progress': 'In Progress',
                                'Completed': 'Completed',
                                'Blocked': 'Blocked',
                                'On Hold': 'On Hold'
                            }, value='All').classes('w-48').props('outlined dense')
                            
                            query_input = ui.input(placeholder='Search tasks...').classes('w-64').props('outlined dense color=primary')
                            
                        def run_filter():
                            f_db = SessionLocal()
                            try:
                                # Apply period filters
                                p = period_filter.value
                                today = date.today()
                                s_date, e_date = None, None
                                if p == 'today':
                                    s_date = today
                                elif p == 'yesterday':
                                    s_date = today - timedelta(days=1)
                                    e_date = today - timedelta(days=1)
                                elif p == 'last_week':
                                    s_date = today - timedelta(days=7)
                                elif p == 'last_month':
                                    s_date = today - timedelta(days=30)
                                    
                                res = get_filtered_tasks(
                                    db=f_db,
                                    employee_id=emp_id,
                                    status_filter=status_filter.value,
                                    query_str=query_input.value,
                                    start_date=s_date,
                                    end_date=e_date
                                )
                                table.rows = [{
                                    'task_id': t.task_id,
                                    'date': t.created_date.strftime('%Y-%m-%d'),
                                    'time': t.created_time.strftime('%I:%M %p'),
                                    'title': t.title,
                                    'description': t.description or 'No description.',
                                    'status': t.status,
                                    'is_today': t.created_date == today
                                } for t in res]
                            finally:
                                f_db.close()
                                
                        period_filter.on('change', run_filter)
                        status_filter.on('change', run_filter)
                        query_input.on('change', run_filter)
                        
                        ui.button('Search', icon='search', on_click=run_filter).props('flat color=primary')

                    # History Table
                    columns = [
                        {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'center', 'sortable': True},
                        {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'center'},
                        {'name': 'title', 'label': 'Task Title', 'field': 'title', 'align': 'left', 'sortable': True},
                        {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                    ]

                    table = ui.table(columns=columns, rows=rows, row_key='task_id').classes('w-full glass-card p-4').props('flat')
                    
                    # Custom chips for status
                    table.add_slot('body-cell-status', '''
                        <q-td :props="props">
                            <span :class="'badge-status badge-' + (props.value === 'Completed' ? 'completed' : props.value === 'Work In Progress' ? 'wip' : props.value === 'Blocked' ? 'blocked' : props.value === 'On Hold' ? 'hold' : 'pending')">
                                {{ props.value }}
                            </span>
                        </q-td>
                    ''')
                    
                    # Custom action: Edit is enabled ONLY for today's tasks
                    table.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn v-if="props.row.is_today" flat round dense color="primary" icon="edit" @click="$parent.$emit('edit_hist_task', props.row)">
                                <q-tooltip class="bg-indigo text-white">Edit Task</q-tooltip>
                            </q-btn>
                            <span v-else class="text-xs text-gray-500 italic">Locked</span>
                        </q-td>
                    ''')

                    def handle_edit_hist(row_data):
                        # Simple helper to reload the current page upon edit success
                        def reload_hist():
                            ui.navigate.to('/employee/history')
                        # Import inner add/edit from employee dashboard variables (or write it explicitly here)
                        open_edit_task_modal_internal(row_data, callback=reload_hist)
                        
                    table.on('edit_hist_task', lambda msg: handle_edit_hist(msg.args))

                # PANEL 2: CALENDAR VIEW
                with ui.tab_panel(calendar_tab).classes('p-0 bg-transparent'):
                    with ui.element('div').classes('glass-card p-6 w-full'):
                        ui.label('Monthly Activity Tracker').classes('text-lg font-semibold mb-4')
                        
                        # FullCalendar CDN scripts inclusion
                        ui.add_head_html('<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">')
                        ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>')
                        
                        # Target DIV
                        ui.html('<div id="calendar-element" style="max-width: 900px; margin: 0 auto; color: #0F172A;"></div>').classes('w-full p-2')
                        
                        # Inject JS Initialization script
                        js_events = json.dumps(events)
                        ui.run_javascript(f"""
                            setTimeout(() => {{
                                var calendarEl = document.getElementById('calendar-element');
                                if (calendarEl) {{
                                    var calendar = new FullCalendar.Calendar(calendarEl, {{
                                        initialView: 'dayGridMonth',
                                        themeSystem: 'standard',
                                        height: 550,
                                        headerToolbar: {{
                                            left: 'prev,next today',
                                            center: 'title',
                                            right: 'dayGridMonth,listMonth'
                                        }},
                                        events: {js_events},
                                        eventDidMount: function(info) {{
                                            info.el.style.borderRadius = '6px';
                                            info.el.style.padding = '2px 6px';
                                            info.el.style.fontSize = '11px';
                                            info.el.style.fontWeight = 'bold';
                                        }}
                                    }});
                                    calendar.render();
                                }}
                            }}, 300);
                        """)

            # Shared modal helper for editing a history task
            def open_edit_task_modal_internal(row_data, callback=None):
                with ui.dialog().classes('w-full max-w-lg') as dialog, ui.card().classes('glass-card p-6 w-full'):
                    ui.label('Edit Task Update').classes('text-xl font-bold mb-4')
                    
                    t_title = ui.input('Task Title', value=row_data['title']).classes('w-full mb-3').props('outlined color=primary')
                    t_desc = ui.textarea('Task Description', value=row_data['description']).classes('w-full mb-3').props('outlined color=primary')
                    t_status = ui.select({
                        'Pending': 'Pending',
                        'Work In Progress': 'Work In Progress',
                        'Completed': 'Completed',
                        'Blocked': 'Blocked',
                        'On Hold': 'On Hold'
                    }, value=row_data['status']).classes('w-full mb-6').props('outlined')

                    def save():
                        if not t_title.value:
                            ui.notify('Task Title is required', type='warning')
                            return
                            
                        s_db = SessionLocal()
                        try:
                            ok, msg = update_task(
                                db=s_db,
                                employee_id=emp_id,
                                task_id=row_data['task_id'],
                                title=t_title.value,
                                description=t_desc.value,
                                status=t_status.value
                            )
                            if ok:
                                ui.notify(msg, type='positive')
                                dialog.close()
                                if callback:
                                    callback()
                            else:
                                ui.notify(msg, type='negative')
                        finally:
                            s_db.close()

                    with ui.row().classes('w-full justify-end mt-4 gap-2'):
                        ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                        ui.button('Update Task', on_click=save).classes('btn-neon')
                dialog.open()


    @ui.page('/employee/profile')
    def employee_profile():
        # Authenticate employee
        if not app.storage.user.get('authenticated', False):
            ui.navigate.to('/login')
            return
            
        emp_id = app.storage.user.get('employee_id')
        
        db = SessionLocal()
        try:
            emp = get_employee_by_id(db, emp_id)
        finally:
            db.close()

        with render_layout('/employee/profile'):
            
            # Header
            with ui.row().classes('w-full items-center justify-between mb-8'):
                with ui.element('div'):
                    ui.label('Employee Profile').classes('text-3xl font-bold tracking-tight')
                    ui.label('View registration data and update account password').classes('text-gray-500 text-sm')

            # Content grid
            with ui.grid().classes('grid-cols-1 md:grid-cols-3 gap-6 w-full'):
                
                # Column 1: Info card
                with ui.element('div').classes('glass-card p-6 col-span-1 md:col-span-2'):
                    ui.label('Profile Details').classes('text-xl font-bold mb-6')
                    
                    with ui.grid().classes('grid-cols-2 gap-4'):
                        with ui.element('div'):
                            ui.label('Employee ID').classes('text-gray-500 text-xs')
                            ui.label(emp.employee_id).classes('font-semibold text-base')
                            
                        with ui.element('div'):
                            ui.label('Full Name').classes('text-gray-500 text-xs')
                            ui.label(emp.employee_name).classes('font-semibold text-base')
                            
                        with ui.element('div'):
                            ui.label('Phone Number').classes('text-gray-500 text-xs')
                            ui.label(emp.phone_number).classes('font-semibold text-base')
                            
                        with ui.element('div'):
                            ui.label('Role Privilege').classes('text-gray-500 text-xs')
                            ui.label(emp.role.upper()).classes('text-primary font-bold text-base')
                            
                        with ui.element('div'):
                            ui.label('Department').classes('text-gray-500 text-xs')
                            ui.label(emp.department or 'N/A').classes('font-semibold text-base')
                            
                        with ui.element('div'):
                            ui.label('Joining Date').classes('text-gray-500 text-xs')
                            ui.label(emp.joining_date.strftime('%Y-%m-%d')).classes('font-semibold text-base')
                            
                # Column 2: Password change card
                with ui.element('div').classes('glass-card p-6 col-span-1'):
                    ui.label('Security Credentials').classes('text-xl font-bold mb-6')
                    
                    old_pwd = ui.input('Current Password', password=True).classes('w-full mb-3').props('outlined color=primary')
                    new_pwd = ui.input('New Password', password=True).classes('w-full mb-3').props('outlined color=primary')
                    confirm_pwd = ui.input('Confirm New Password', password=True).classes('w-full mb-6').props('outlined color=primary')
                    
                    def submit_change():
                        if not old_pwd.value or not new_pwd.value or not confirm_pwd.value:
                            ui.notify('All fields are required', type='warning')
                            return
                            
                        if new_pwd.value != confirm_pwd.value:
                            ui.notify('New passwords do not match!', type='warning')
                            return
                            
                        if len(new_pwd.value) < 6:
                            ui.notify('Password must be at least 6 characters long', type='warning')
                            return
                            
                        s_db = SessionLocal()
                        try:
                            ok, msg = change_user_password(
                                db=s_db,
                                employee_id=emp_id,
                                old_password=old_pwd.value,
                                new_password=new_pwd.value
                            )
                            if ok:
                                ui.notify(msg, type='positive')
                                old_pwd.value = ''
                                new_pwd.value = ''
                                confirm_pwd.value = ''
                            else:
                                ui.notify(msg, type='negative')
                        finally:
                            s_db.close()
                            
                    ui.button('Update Password', on_click=submit_change).classes('w-full btn-neon')
