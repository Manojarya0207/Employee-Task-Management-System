from nicegui import app, ui
from models import SessionLocal
from controllers.task_controller import TaskController
from controllers.status_controller import StatusController
from controllers.employee_controller import EmployeeController
from controllers.auth_controller import AuthController
from pages.layout import render_layout
from repositories.employee_repository import EmployeeRepository
from datetime import date, datetime, timedelta, time
import json

def parse_time_string(val):
    if not isinstance(val, str):
        return val
    try:
        return time.fromisoformat(val)
    except ValueError:
        try:
            return datetime.strptime(val, '%H:%M:%S.%f').time()
        except ValueError:
            return datetime.strptime(val, '%H:%M:%S').time()


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
CLASS_WFULL_ITEMS_JUSTIFY_MB8 = 'w-full items-center justify-between mb-8 responsive-page-header'
CLASS_WFULL_JUSTIFY_END_GAP2 = 'w-full justify-end mt-4 gap-2 responsive-actions'
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

# Module-level Modal Helpers
def open_add_task_modal(callback=None):
    emp_id = app.storage.user.get('employee_id')
    db = SessionLocal()
    try:
        res = StatusController.get_task_statuses(db)
        statuses = res["data"] if res["success"] else []
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
            
            status_options = {s['name']: s['name'] for s in statuses}
            t_status = ui.select(status_options, value=statuses[0]['name']).classes(CLASS_WFULL_MB6).props('outlined')

            def save():
                if not t_title.value:
                    ui.notify(MSG_TITLE_REQUIRED, type='warning')
                    return
                    
                s_db = SessionLocal()
                try:
                    res_add = TaskController.add(
                        db=s_db,
                        employee_id=emp_id,
                        title=t_title.value,
                        description=t_desc.value,
                        status=t_status.value
                    )
                    if res_add["success"]:
                        ui.notify(res_add["message"], type='positive')
                        dialog.close()
                        if callback:
                            callback()
                        else:
                            ui.navigate.to(PATH_EMPLOYEE)
                    else:
                        ui.notify(res_add["message"], type='negative')
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
        res = StatusController.get_task_statuses(db)
        statuses = res["data"] if res["success"] else []
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
            
            status_options = {s['name']: s['name'] for s in statuses}
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
                    res_up = TaskController.update(
                        db=s_db,
                        employee_id=emp_id,
                        task_id=row_data['task_id'],
                        title=t_title.value,
                        description=t_desc.value,
                        status=t_status.value
                    )
                    if res_up["success"]:
                        ui.notify(res_up["message"], type='positive')
                        dialog.close()
                        if callback:
                            callback()
                    else:
                        ui.notify(res_up["message"], type='negative')
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
        emp_profile = EmployeeRepository.get_by_id(db, emp_id)
        
        # Fetch task statuses
        res_statuses = StatusController.get_task_statuses(db)
        statuses = res_statuses["data"] if res_statuses["success"] else []
        has_statuses = len(statuses) > 0
        status_colors = {s['name']: s['color'] for s in statuses}
        
        # Fetch today's tasks
        res_tasks = TaskController.get_filtered(db, employee_id=emp_id, start_date=today, end_date=today)
        today_tasks = res_tasks["data"] if res_tasks["success"] else []
        
        today_count = len(today_tasks)
        completed_count = 0
        wip_count = 0
        pending_count = 0
        for t in today_tasks:
            status_lower = t['status'].lower()
            if 'completed' in status_lower:
                completed_count += 1
            elif 'wip' in status_lower or 'progress' in status_lower:
                wip_count += 1
            else:
                pending_count += 1
        
        # This week's tasks count
        start_of_week = today - timedelta(days=today.weekday())
        res_week = TaskController.get_filtered(db, employee_id=emp_id, start_date=start_of_week)
        week_tasks_count = len(res_week["data"]) if res_week["success"] else 0
        
        # Check reminder requirement (If past 6:00 PM and no submissions today)
        show_reminder = False
        current_hour = datetime.now().hour
        if today_count == 0 and current_hour >= 18:
            show_reminder = True

        rows = []
        for t in today_tasks:
            # Parse times safely
            t_time_parsed = parse_time_string(t['created_time'])
            rows.append({
                'task_id': t['task_id'],
                'title': t['title'],
                'description': t['description'] or 'No description provided.',
                'status': t['status'],
                'status_color': status_colors.get(t['status'], '#6b7280'),
                'time': t_time_parsed.strftime(TIME_FORMAT_12H) if hasattr(t_time_parsed, 'strftime') else str(t_time_parsed),
                'last_modified': t['created_time']  # Placeholder for simple display
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

            # Render custom description wrap
            table.add_slot('body-cell-description', '''
                <q-td :props="props">
                    <div style="white-space: normal; word-break: break-word; max-width: 450px; min-width: 200px; text-align: left;">
                        {{ props.value }}
                    </div>
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
        res_statuses = StatusController.get_task_statuses(db)
        statuses = res_statuses["data"] if res_statuses["success"] else []
        status_colors = {s['name']: s['color'] for s in statuses}
        
        res_tasks = TaskController.get_employee_tasks(db, emp_id)
        tasks = res_tasks["data"] if res_tasks["success"] else []
        
        res_events = TaskController.get_calendar_events(db, emp_id)
        events = res_events["data"] if res_events["success"] else []
        
        rows = []
        for t in tasks:
            t_date = datetime.strptime(t['created_date'], '%Y-%m-%d').date() if isinstance(t['created_date'], str) else t['created_date']
            t_time = parse_time_string(t['created_time'])
            rows.append({
                'task_id': t['task_id'],
                'date': t_date.strftime(DATE_FORMAT),
                'time': t_time.strftime(TIME_FORMAT_12H),
                'title': t['title'],
                'description': t['description'] or 'No description.',
                'status': t['status'],
                'status_color': status_colors.get(t['status'], '#6b7280'),
                'is_today': t_date == date.today()
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
                with ui.row().classes('w-full mb-6 items-center justify-between gap-4 responsive-toolbar'):
                    with ui.row().classes('items-center gap-3 responsive-toolbar'):
                        period_filter = ui.select({
                            'all': 'All History',
                            'today': 'Today Only',
                            'yesterday': 'Yesterday',
                            'last_week': 'Last 7 Days',
                            'last_month': 'Last 30 Days'
                        }, value='all').classes('w-48').props('outlined dense')
                        
                        status_filter_options = {'All': 'All Statuses'}
                        for s in statuses:
                            status_filter_options[s['name']] = s['name']
                        
                        status_filter = ui.select(status_filter_options, value='All').classes('w-48').props('outlined dense')
                        query_input = ui.input(placeholder='Search tasks...').classes('w-64').props('outlined dense color=primary')
                        
                    def run_filter():
                        f_db = SessionLocal()
                        try:
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
                                
                            res_filtered = TaskController.get_filtered(
                                db=f_db,
                                employee_id=emp_id,
                                start_date=s_date,
                                end_date=e_date,
                                status=status_filter.value if status_filter.value != 'All' else None,
                                query_str=query_input.value.strip() if query_input.value else None
                            )
                            filtered = res_filtered["data"] if res_filtered["success"] else []
                            
                            res_f_statuses = StatusController.get_task_statuses(f_db)
                            f_statuses = res_f_statuses["data"] if res_f_statuses["success"] else []
                            f_status_colors = {s['name']: s['color'] for s in f_statuses}
                            
                            t_rows = []
                            for t in filtered:
                                t_date = datetime.strptime(t['created_date'], '%Y-%m-%d').date() if isinstance(t['created_date'], str) else t['created_date']
                                t_time = parse_time_string(t['created_time'])
                                t_rows.append({
                                    'task_id': t['task_id'],
                                    'date': t_date.strftime(DATE_FORMAT),
                                    'time': t_time.strftime(TIME_FORMAT_12H),
                                    'title': t['title'],
                                    'description': t['description'] or 'No description.',
                                    'status': t['status'],
                                    'status_color': f_status_colors.get(t['status'], '#6b7280'),
                                    'is_today': t_date == today
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

                # Custom description wrap
                table.add_slot('body-cell-description', '''
                    <q-td :props="props">
                        <div style="white-space: normal; word-break: break-word; max-width: 450px; min-width: 200px; text-align: left;">
                            {{ props.value }}
                        </div>
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
                    
                    ui.add_head_html('<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">')
                    ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>')
                    
                    ui.html('<div id="calendar-element" style="max-width: 900px; margin: 0 auto; color: #0F172A;"></div>').classes('w-full p-2')
                    
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
        emp = EmployeeRepository.get_by_id(db, emp_id)
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
                        ui.label(emp.joining_date.strftime(DATE_FORMAT) if emp.joining_date else 'N/A').classes(CLASS_FONT_SEMIBOLD_BASE)
                        
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
                        res_pwd = AuthController.change_password(
                            db=s_db,
                            employee_id=emp_id,
                            old_password=old_pwd.value,
                            new_password=new_pwd.value
                        )
                        if res_pwd["success"]:
                            ui.notify(res_pwd["message"], type='positive')
                            old_pwd.value = ''
                            new_pwd.value = ''
                            confirm_pwd.value = ''
                        else:
                            ui.notify(res_pwd["message"], type='negative')
                    finally:
                        s_db.close()
                        
                ui.button('Update Password', on_click=submit_change).classes('w-full btn-neon')


def init_employee_routes():
    pass
