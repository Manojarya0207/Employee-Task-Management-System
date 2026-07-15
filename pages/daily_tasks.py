from nicegui import app, ui
from models import SessionLocal
from pages.layout import render_layout
from datetime import date
from controllers.task_controller import TaskController
from controllers.status_controller import StatusController

def init_daily_tasks_routes():
    # Trigger importing of page
    pass

@ui.page('/admin/daily-tasks')
def view_daily_tasks():
    # Authenticate and authorize admin
    if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
        ui.navigate.to('/login')
        return

    # Helper function to get today's tasks and stats
    def get_today_data():
        db = SessionLocal()
        try:
            res_tasks = TaskController.get_daily_tasks_data(db)
            res_statuses = StatusController.get_task_statuses(db)
            
            tasks = res_tasks["data"] if res_tasks["success"] else []
            statuses = res_statuses["data"] if res_statuses["success"] else []
            status_colors = {s["name"]: s["color"] for s in statuses}
            
            rows = []
            completed = 0
            wip = 0
            pending = 0
            blocked = 0
            on_hold = 0

            for t in tasks:
                rows.append({
                    'task_id': t['task_id'],
                    'time': t['time'],
                    'employee_id': t['employee_id'],
                    'employee_name': t['employee_name'],
                    'department': t['department'],
                    'title': t['title'],
                    'description': t['description'],
                    'status': t['status'],
                    'status_color': status_colors.get(t['status'], '#6b7280')
                })
                # Stats calculation
                status_lower = t['status'].lower()
                if 'completed' in status_lower:
                    completed += 1
                elif 'wip' in status_lower or 'progress' in status_lower:
                    wip += 1
                elif 'blocked' in status_lower:
                    blocked += 1
                elif 'hold' in status_lower:
                    on_hold += 1
                else:
                    pending += 1

            return rows, len(tasks), completed, wip, pending + blocked + on_hold
        finally:
            db.close()

    rows, total, completed, wip, other = get_today_data()

    with render_layout('/admin/daily-tasks'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-8 responsive-page-header'):
            with ui.element('div'):
                ui.label("Today's Tasks").classes('text-3xl font-bold tracking-tight')
                ui.label(f"Monitor employee tasks submitted today ({date.today().strftime('%B %d, %Y')})").classes('text-gray-500 text-sm')

        # Stats Cards
        with ui.row().classes('w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8'):
            # Total Card
            with ui.element('div').classes('glass-card p-6 metric-card flex items-center gap-4'):
                ui.element('i').classes('ri-article-line text-3xl text-primary bg-primary/10 p-3 rounded-xl')
                with ui.element('div'):
                    total_label = ui.label(str(total)).classes('text-2xl font-bold text-slate-800')
                    ui.label('Total Submitted').classes('text-xs text-gray-500 font-semibold uppercase tracking-wider')

            # Completed Card
            with ui.element('div').classes('glass-card p-6 metric-card flex items-center gap-4'):
                ui.element('i').classes('ri-checkbox-circle-line text-3xl text-emerald-500 bg-emerald-50 p-3 rounded-xl')
                with ui.element('div'):
                    completed_label = ui.label(str(completed)).classes('text-2xl font-bold text-slate-800')
                    ui.label('Completed').classes('text-xs text-gray-500 font-semibold uppercase tracking-wider')

            # WIP Card
            with ui.element('div').classes('glass-card p-6 metric-card flex items-center gap-4'):
                ui.element('i').classes('ri-time-line text-3xl text-blue-500 bg-blue-50 p-3 rounded-xl')
                with ui.element('div'):
                    wip_label = ui.label(str(wip)).classes('text-2xl font-bold text-slate-800')
                    ui.label('In Progress').classes('text-xs text-gray-500 font-semibold uppercase tracking-wider')

            # Pending/Blocked/On Hold Card
            with ui.element('div').classes('glass-card p-6 metric-card flex items-center gap-4'):
                ui.element('i').classes('ri-alert-line text-3xl text-amber-500 bg-amber-50 p-3 rounded-xl')
                with ui.element('div'):
                    other_label = ui.label(str(other)).classes('text-2xl font-bold text-slate-800')
                    ui.label('Pending / Other').classes('text-xs text-gray-500 font-semibold uppercase tracking-wider')

        # Filter Control
        with ui.element('div').classes('glass-card p-6 w-full mb-6'):
            search_input = ui.input(placeholder='Search by employee, task title, or description...').classes('w-full').props('outlined dense color=primary')

        # Columns
        columns = [
            {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'center', 'sortable': True},
            {'name': 'employee', 'label': 'Employee', 'field': 'employee_name', 'align': 'left', 'sortable': True},
            {'name': 'department', 'label': 'Department', 'field': 'department', 'align': 'left', 'sortable': True},
            {'name': 'task_details', 'label': 'Task Details', 'field': 'title', 'align': 'left'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True}
        ]

        # Table
        table = ui.table(columns=columns, rows=rows, row_key='task_id').classes('w-full glass-card p-4').props('flat')

        # Custom cell slot for employee details
        table.add_slot('body-cell-employee', '''
            <q-td :props="props">
                <div class="font-bold text-slate-900">{{ props.row.employee_name }}</div>
                <div class="text-xs text-gray-500">ID: {{ props.row.employee_id }}</div>
            </q-td>
        ''')

        # Custom cell slot for task title & description
        table.add_slot('body-cell-task_details', '''
            <q-td :props="props">
                <div class="font-bold text-slate-900">{{ props.row.title }}</div>
                <div class="text-xs text-gray-600 text-wrap" style="max-width: 450px;">{{ props.row.description }}</div>
            </q-td>
        ''')

        # Custom cell slot for status
        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <span class="badge-status" :style="{ backgroundColor: props.row.status_color, color: '#fff', padding: '4px 12px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 'bold' }">
                    {{ props.value }}
                </span>
            </q-td>
        ''')

        # Refresh filter function
        def run_filter():
            q = (search_input.value or '').lower()
            all_rows, new_total, new_completed, new_wip, new_other = get_today_data()
            
            # Filter rows
            filtered_rows = []
            for r in all_rows:
                if (not q or q in r['employee_name'].lower() or q in r['employee_id'].lower() 
                    or q in r['title'].lower() or q in r['description'].lower() or q in r['department'].lower()):
                    filtered_rows.append(r)
            
            table.rows = filtered_rows
            # Update stats labels
            total_label.text = str(new_total)
            completed_label.text = str(new_completed)
            wip_label.text = str(new_wip)
            other_label.text = str(new_other)

        search_input.on('change', run_filter)
        search_input.on('keyup', run_filter)
