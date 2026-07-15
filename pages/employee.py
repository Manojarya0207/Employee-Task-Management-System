from nicegui import app, ui
from models import SessionLocal
from models.task import Task
from models.employee import Employee
from models.status import TaskStatus
from services.task_service import (
    get_employee_tasks, add_task, update_task, 
    get_filtered_tasks, get_tasks_by_period, get_calendar_events
)
from services.auth_service import change_user_password
from services.employee_service import get_employee_by_id
from pages.layout import render_layout
from datetime import date, datetime, timedelta
import json

# Constants to avoid duplicated string literal smells
STATUS_COMPLETED = 'Completed'
STATUS_PENDING = 'Pending'
STATUS_WIP = 'Work In Progress'
STATUS_BLOCKED = 'Blocked'
STATUS_HOLD = 'On Hold'

PATH_LOGIN = '/login'
PATH_EMPLOYEE = '/employee'
PATH_EMPLOYEE_HISTORY = '/employee/history'

CLASS_GLASS_CARD_METRIC = 'glass-card p-6 metric-card'
CLASS_GLASS_CARD_WFULL = 'glass-card p-6 w-full'
CLASS_WFULL_ITEMS_JUSTIFY_MB8 = 'w-full items-center justify-between mb-8'
CLASS_WFULL_JUSTIFY_END_GAP2 = 'w-full justify-end mt-4 gap-2'
CLASS_TEXT_GRAY_500_SM = 'text-gray-500 text-sm'
CLASS_TEXT_GRAY_500_SM_BOLD = 'text-gray-500 text-sm font-semibold'
CLASS_TEXT_GRAY_500_XS = 'text-gray-500 text-xs'
CLASS_TEXT_GRAY_500_XS_MT1 = 'text-gray-500 text-xs mt-1'
CLASS_TEXT_XL_BOLD_MB4 = 'text-xl font-bold mb-4'
CLASS_FONT_SEMIBOLD_BASE = 'font-semibold text-base'
CLASS_WFULL_MB3 = 'w-full mb-3'
CLASS_WFULL_MB6 = 'w-full mb-6'

CLASS_WFULL_MAX_LG = 'w-full max-w-lg'

MSG_TITLE_REQUIRED = 'Task Title is required'
DESC_TASK_DESCRIPTION = 'Task Description'
TIME_FORMAT_12H = '%I:%M %p'
DATE_FORMAT = '%Y-%m-%d'

STATUS_OPTIONS = {
    STATUS_PENDING: STATUS_PENDING,
    STATUS_WIP: STATUS_WIP,
    STATUS_COMPLETED: STATUS_COMPLETED,
    STATUS_BLOCKED: STATUS_BLOCKED,
    STATUS_HOLD: STATUS_HOLD
}

# Module-level Modal Helpers
def open_add_task_modal(callback=None):
    emp_id = app.storage.user.get('employee_id')
    db = SessionLocal()
    try:
        statuses = db.query(TaskStatus).all()
    finally:
        db.close()

    with ui.dialog().classes(CLASS_WFULL_MAX_LG) as dialog, ui.card().classes(CLASS_GLASS_CARD_WFULL):
        if not statuses:
            ui.label('Wait for Admin Update').classes('text-xl font-bold text-red-500 mb-4')
            ui.label('No task statuses are currently defined by the administrator. Please wait for an admin update.').classes(CLASS_TEXT_GRAY_500_SM)
            with ui.row().classes(CLASS_WFULL_JUSTIFY_END_GAP2):
                ui.button('Close', on_click=dialog.close).props('flat color=primary')
        else:
            ui.label('Add Task Update').classes(CLASS_TEXT_XL_BOLD_MB4)
            
            t_title = ui.input('Task Title').classes(CLASS_WFULL_MB3).props('outlined color=primary')
            t_desc = ui.textarea(DESC_TASK_DESCRIPTION).classes(CLASS_WFULL_MB3).props('outlined color=primary')
            
            status_options = {s.name: s.name for s in statuses}
            t_status = ui.select(status_options, value=statuses[0].name).classes(CLASS_WFULL_MB6).props('outlined')

            def save():
                if not t_title.value:
                    ui.notify(MSG_TITLE_REQUIRED, type='warning')
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
                        if callback:
                            callback()
                        else:
                            ui.navigate.to(PATH_EMPLOYEE)
                    else:
                        ui.notify(msg, type='negative')
                finally:
                    s_db.close()

            with ui.row().classes(CLASS_WFULL_JUSTIFY_END_GAP2):
                ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                ui.button('Submit Task', on_click=save).classes('btn-neon')
    dialog.open()

def open_edit_task_modal(row_data, callback=None):
    emp_id = app.storage.user.get('employee_id')
    db = SessionLocal()
    try:
        statuses = db.query(TaskStatus).all()
    finally:
        db.close()

    with ui.dialog().classes(CLASS_WFULL_MAX_LG) as dialog, ui.card().classes(CLASS_GLASS_CARD_WFULL):
        if not statuses:
            ui.label('Wait for Admin Update').classes('text-xl font-bold text-red-500 mb-4')
            ui.label('No task statuses are currently defined by the administrator. Please wait for an admin update.').classes(CLASS_TEXT_GRAY_500_SM)
            with ui.row().classes(CLASS_WFULL_JUSTIFY_END_GAP2):
                ui.button('Close', on_click=dialog.close).props('flat color=primary')
        else:
            ui.label('Edit Task Update').classes(CLASS_TEXT_XL_BOLD_MB4)
            
            t_title = ui.input('Task Title', value=row_data['title']).classes(CLASS_WFULL_MB3).props('outlined color=primary')
            t_desc = ui.textarea(DESC_TASK_DESCRIPTION, value=row_data['description']).classes(CLASS_WFULL_MB3).props('outlined color=primary')
            
            status_options = {s.name: s.name for s in statuses}
            current_status = row_data['status']
            if current_status not in status_options:
                status_options[current_status] = current_status
            t_status = ui.select(status_options, value=current_status).classes(CLASS_WFULL_MB6).props('outlined')

            def save():
                if not t_title.value:
                    ui.notify(MSG_TITLE_REQUIRED, type='warning')
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

            with ui.row().classes(CLASS_WFULL_JUSTIFY_END_GAP2):
                ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                ui.button('Update Task', on_click=save).classes('btn-neon')
    dialog.open()


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
        
        # Fetch task statuses
        statuses = db.query(TaskStatus).all()
        has_statuses = len(statuses) > 0
        status_colors = {s.name: s.color for s in statuses}
        
        # Fetch today's tasks
        today_tasks = db.query(Task).filter(
            Task.employee_id == emp_id,
            Task.created_date == today
        ).order_by(Task.created_time.desc()).all()
        
        today_count = len(today_tasks)
        completed_count = 0
        wip_count = 0
        pending_count = 0
        for t in today_tasks:
            status_lower = t.status.lower()
            if 'completed' in status_lower:
                completed_count += 1
            elif 'wip' in status_lower or 'progress' in status_lower:
                wip_count += 1
            else:
                pending_count += 1
        
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
                'status_color': status_colors.get(t.status, '#6b7280'),
                'time': t.created_time.strftime(TIME_FORMAT_12H),
                'last_modified': t.last_modified.strftime(TIME_FORMAT_12H)
            })
    finally:
        db.close()

    def reload_page():
        ui.navigate.to('/employee')

    # Render layout
    with render_layout(PATH_EMPLOYEE):
        # Admin status alert if no statuses defined
        if not has_statuses:
            with ui.element('div').classes('w-full mb-6 p-6 rounded-xl bg-amber-50 border border-amber-200 flex flex-col gap-2'):
                with ui.row().classes('items-center gap-3'):
                    ui.element('i').classes('ri-alert-line text-amber-500 text-2xl')
                    ui.label('Wait for admin update').classes('text-amber-900 font-bold text-lg')
                ui.label('No task statuses are currently defined. Please wait for the administrator to update task statuses before you can submit tasks.').classes('text-amber-700 text-sm')

        # Reminder banner
        if show_reminder and has_statuses:
            with ui.element('div').classes('w-full mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between'):
                with ui.row().classes('items-center gap-3'):
                    ui.element('i').classes('ri-error-warning-fill text-red-500 text-2xl')
                    with ui.element('div'):
                        ui.label('Daily Submission Reminder!').classes('text-red-900 font-bold')
                        ui.label('You haven\'t logged any work items for today yet. Please submit your updates.').classes('text-red-700 text-xs')
                ui.button('Submit Now', icon='add', on_click=lambda: open_add_task_modal(callback=reload_page)).classes('bg-red-600 hover:bg-red-700 text-white rounded-lg')

        # Header
        with ui.row().classes(CLASS_WFULL_ITEMS_JUSTIFY_MB8):
            with ui.element('div'):
                ui.label(f"Welcome, {emp_profile.employee_name}").classes('text-3xl font-bold tracking-tight')
                ui.label('Log your updates and track daily goals').classes(CLASS_TEXT_GRAY_500_SM)
            
            if has_statuses:
                ui.button('Add Daily Task', icon='add_task', on_click=lambda: open_add_task_modal(callback=reload_page)).classes('btn-neon')
            else:
                ui.button('Add Daily Task', icon='add_task').classes('opacity-50 cursor-not-allowed').props('disabled')

        # Metric grid
        with ui.grid().classes('grid-cols-1 md:grid-cols-4 gap-6 mb-8 w-full'):
            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                ui.label('Logged Today').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                ui.label(str(today_count)).classes('text-4xl font-bold mt-2')
                ui.label('Tasks created today').classes(CLASS_TEXT_GRAY_500_XS_MT1)

            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                ui.label('Completed').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                ui.label(str(completed_count)).classes('text-emerald-600 text-4xl font-bold mt-2')
                ui.label('Goals finished').classes(CLASS_TEXT_GRAY_500_XS_MT1)

            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                ui.label('Pending / WIP').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                ui.label(str(pending_count + wip_count)).classes('text-indigo-600 text-4xl font-bold mt-2')
                ui.label('Work items in progress').classes(CLASS_TEXT_GRAY_500_XS_MT1)

            with ui.element('div').classes(CLASS_GLASS_CARD_METRIC):
                ui.label('This Week Tasks').classes(CLASS_TEXT_GRAY_500_SM_BOLD)
                ui.label(str(week_tasks_count)).classes('text-4xl font-bold mt-2')
                ui.label('Tasks since Monday').classes(CLASS_TEXT_GRAY_500_XS_MT1)

        # Today's Task Table
        ui.label('Today\'s Task Updates').classes(CLASS_TEXT_XL_BOLD_MB4)
        
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
                ui.label('Click "Add Daily Task" to log your updates for today.').classes(CLASS_TEXT_GRAY_500_XS_MT1)
        else:
            table = ui.table(columns=columns, rows=rows, row_key='task_id').classes('w-full glass-card p-4').props('flat hide-bottom')
            
            # Render custom status chip
            table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <span class="badge-status" :style="{ backgroundColor: props.row.status_color, color: '#fff', padding: '4px 12px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 'bold' }">
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

            # Edit Task event handler
            def handle_edit_task_event(row_data):
                open_edit_task_modal(row_data, callback=reload_page)
                
            table.on('edit_task', lambda msg: handle_edit_task_event(msg.args))


@ui.page(PATH_EMPLOYEE_HISTORY)
def task_history():
    # Authenticate employee
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to(PATH_LOGIN)
        return
        
    emp_id = app.storage.user.get('employee_id')
    
    db = SessionLocal()
    try:
        statuses = db.query(TaskStatus).all()
        status_colors = {s.name: s.color for s in statuses}
        
        tasks = get_employee_tasks(db, emp_id)
        events = get_calendar_events(db, emp_id)
        
        rows = []
        for t in tasks:
            rows.append({
                'task_id': t.task_id,
                'date': t.created_date.strftime(DATE_FORMAT),
                'time': t.created_time.strftime(TIME_FORMAT_12H),
                'title': t.title,
                'description': t.description or 'No description.',
                'status': t.status,
                'status_color': status_colors.get(t.status, '#6b7280'),
                'is_today': t.created_date == date.today()
            })
    finally:
        db.close()

    with render_layout(PATH_EMPLOYEE_HISTORY):
        
        # Header
        with ui.row().classes(CLASS_WFULL_ITEMS_JUSTIFY_MB8):
            with ui.element('div'):
                ui.label('Tasks & Submission History').classes('text-3xl font-bold tracking-tight')
                ui.label('Search past reports, filter results, and view visual calendar tracking').classes(CLASS_TEXT_GRAY_500_SM)

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
                        
                        status_filter_options = {'All': 'All Statuses'}
                        for s in statuses:
                            status_filter_options[s.name] = s.name
                        
                        status_filter = ui.select(status_filter_options, value='All').classes('w-48').props('outlined dense')
                        
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
                                e_date = s_date
                            elif p == 'last_week':
                                s_date = today - timedelta(days=7)
                            elif p == 'last_month':
                                s_date = today - timedelta(days=30)
                                
                            filtered = get_filtered_tasks(
                                db=f_db,
                                employee_id=emp_id,
                                start_date=s_date,
                                end_date=e_date,
                                status=status_filter.value if status_filter.value != 'All' else None,
                                search_query=query_input.value.strip() if query_input.value else None
                            )
                            
                            f_statuses = f_db.query(TaskStatus).all()
                            f_status_colors = {s.name: s.color for s in f_statuses}
                            
                            t_rows = []
                            for t in filtered:
                                t_rows.append({
                                    'task_id': t.task_id,
                                    'date': t.created_date.strftime(DATE_FORMAT),
                                    'time': t.created_time.strftime(TIME_FORMAT_12H),
                                    'title': t.title,
                                    'description': t.description or 'No description.',
                                    'status': t.status,
                                    'status_color': f_status_colors.get(t.status, '#6b7280'),
                                    'is_today': t.created_date == today
                                })
                            table.rows = t_rows
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
                        <span class="badge-status" :style="{ backgroundColor: props.row.status_color, color: '#fff', padding: '4px 12px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 'bold' }">
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
                
                def reload_hist():
                    ui.navigate.to(PATH_EMPLOYEE_HISTORY)
                    
                table.on('edit_hist_task', lambda msg: open_edit_task_modal(msg.args, callback=reload_hist))

            # PANEL 2: CALENDAR VIEW
            with ui.tab_panel(calendar_tab).classes('p-0 bg-transparent'):
                with ui.element('div').classes(CLASS_GLASS_CARD_WFULL):
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


@ui.page('/employee/profile')
def employee_profile():
    # Authenticate employee
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to(PATH_LOGIN)
        return
        
    emp_id = app.storage.user.get('employee_id')
    
    db = SessionLocal()
    try:
        emp = get_employee_by_id(db, emp_id)
    finally:
        db.close()

    with render_layout('/employee/profile'):
        
        # Header
        with ui.row().classes(CLASS_WFULL_ITEMS_JUSTIFY_MB8):
            with ui.element('div'):
                ui.label('Employee Profile').classes('text-3xl font-bold tracking-tight')
                ui.label('View registration data and update account password').classes(CLASS_TEXT_GRAY_500_SM)

        # Content grid
        with ui.grid().classes('grid-cols-1 md:grid-cols-3 gap-6 w-full'):
            
            # Column 1: Info card
            with ui.element('div').classes('glass-card p-6 col-span-1 md:col-span-2'):
                ui.label('Profile Details').classes('text-xl font-bold mb-6')
                
                with ui.grid().classes('grid-cols-2 gap-4'):
                    with ui.element('div'):
                        ui.label('Employee ID').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.employee_id).classes(CLASS_FONT_SEMIBOLD_BASE)
                        
                    with ui.element('div'):
                        ui.label('Full Name').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.employee_name).classes(CLASS_FONT_SEMIBOLD_BASE)
                        
                    with ui.element('div'):
                        ui.label('Phone Number').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.phone_number).classes(CLASS_FONT_SEMIBOLD_BASE)
                        
                    with ui.element('div'):
                        ui.label('Role Privilege').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.role.upper()).classes('text-primary font-bold text-base')
                        
                    with ui.element('div'):
                        ui.label('Department').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.department or 'N/A').classes(CLASS_FONT_SEMIBOLD_BASE)
                        
                    with ui.element('div'):
                        ui.label('Joining Date').classes(CLASS_TEXT_GRAY_500_XS)
                        ui.label(emp.joining_date.strftime(DATE_FORMAT)).classes(CLASS_FONT_SEMIBOLD_BASE)
                        
            # Column 2: Password change card
            with ui.element('div').classes('glass-card p-6 col-span-1'):
                ui.label('Security Credentials').classes('text-xl font-bold mb-6')
                
                old_pwd = ui.input('Current Password', password=True).classes(CLASS_WFULL_MB3).props('outlined color=primary')
                new_pwd = ui.input('New Password', password=True).classes(CLASS_WFULL_MB3).props('outlined color=primary')
                confirm_pwd = ui.input('Confirm New Password', password=True).classes(CLASS_WFULL_MB6).props('outlined color=primary')
                
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


def init_employee_routes():
    pass
