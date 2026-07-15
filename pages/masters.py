from nicegui import app, ui
from models import SessionLocal
from pages.layout import render_layout
from controllers.status_controller import StatusController

def init_masters_routes():
    pass

def render_master_page(status_type, page_title, page_subtitle, active_route):
    """
    Helper to render a complete status master management page with CRUD operations.
    """
    if not app.storage.user.get('authenticated', False) or app.storage.user.get('role') != 'admin':
        ui.navigate.to('/login')
        return

    def get_all_records():
        db = SessionLocal()
        try:
            if status_type == 'task':
                res = StatusController.get_task_statuses(db)
            else:
                res = StatusController.get_employee_statuses(db)
            return res["data"] if res["success"] else []
        finally:
            db.close()

    records = get_all_records()
    rows = [{'id': r['name'], 'name': r['name'], 'description': r['description'] or '', 'color': r['color']} for r in records]

    with render_layout(active_route):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-8 responsive-page-header'):
            with ui.element('div'):
                ui.label(page_title).classes('text-3xl font-bold tracking-tight')
                ui.label(page_subtitle).classes('text-gray-500 text-sm')
            ui.button('Add New Status', icon='add', on_click=lambda: open_dialog()).classes('btn-neon bg-primary text-white')

        # Search / Filter Bar
        with ui.element('div').classes('glass-card p-4 w-full mb-6'):
            search_input = ui.input(placeholder='Search by name or description...').classes('w-full').props('outlined dense color=primary')

        # Columns
        columns = [
            {'name': 'name', 'label': 'Status Name', 'field': 'name', 'align': 'left', 'sortable': True},
            {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
            {'name': 'color', 'label': 'Badge Preview', 'field': 'color', 'align': 'center'},
            {'name': 'actions', 'label': 'Actions', 'field': 'id', 'align': 'right'}
        ]

        # Table
        table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full glass-card p-4').props('flat')

        # Custom cell slot for name
        table.add_slot('body-cell-name', '''
            <q-td :props="props">
                <div class="font-bold text-slate-900">{{ props.value }}</div>
            </q-td>
        ''')

        # Custom cell slot for color badge
        table.add_slot('body-cell-color', '''
            <q-td :props="props">
                <span class="badge-status" :style="{ backgroundColor: props.value, color: '#fff', padding: '4px 12px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 'bold' }">
                    {{ props.row.name }}
                </span>
            </q-td>
        ''')

        # Custom cell slot for actions
        table.add_slot('body-cell-actions', '''
            <q-td :props="props" class="q-gutter-xs">
                <q-btn flat round color="primary" icon="edit" @click="() => $parent.$emit('edit_record', props.row)"></q-btn>
                <q-btn flat round color="negative" icon="delete" @click="() => $parent.$emit('delete_record', props.row)"></q-btn>
            </q-td>
        ''')

        def filter_records():
            query_str = (search_input.value or '').lower()
            all_recs = get_all_records()
            filtered = []
            for r in all_recs:
                if not query_str or query_str in r['name'].lower() or (r['description'] and query_str in r['description'].lower()):
                    filtered.append({'id': r['name'], 'name': r['name'], 'description': r['description'] or '', 'color': r['color']})
            table.rows = filtered

        search_input.on('change', filter_records)
        search_input.on('keyup', filter_records)

        # Define suggestions based on status type
        suggestions = []
        if status_type == 'task':
            suggestions = [
                {'name': 'Pending', 'desc': 'Task has been created but not started', 'color': '#eab308'},
                {'name': 'Work In Progress', 'desc': 'Task is currently being worked on', 'color': '#3b82f6'},
                {'name': 'Completed', 'desc': 'Task has been successfully completed', 'color': '#10b981'},
                {'name': 'Blocked', 'desc': 'Task is blocked by dependency or issue', 'color': '#ef4444'},
                {'name': 'On Hold', 'desc': 'Task is temporarily suspended', 'color': '#8b5cf6'}
            ]
        else:
            suggestions = [
                {'name': 'active', 'desc': 'Employee is active and working', 'color': '#10b981'},
                {'name': 'inactive', 'desc': 'Employee has left or is inactive', 'color': '#ef4444'},
                {'name': 'On Leave', 'desc': 'Employee is currently on approved leave', 'color': '#f59e0b'}
            ]

        # Dialog for Add / Edit
        dialog = ui.dialog()
        with dialog, ui.card().classes('w-full max-w-md p-6 glass-card'):
            dialog_title = ui.label('').classes('text-xl font-bold mb-4 text-slate-800')
            name_input = ui.input('Status Name').classes('w-full mb-2').props('outlined dense color=primary')
            
            # Predefined suggestions row
            if suggestions:
                ui.label('Quick Presets:').classes('text-xs text-gray-500 mb-1')
                with ui.row().classes('w-full flex-wrap gap-2 mb-4'):
                    for sugg in suggestions:
                        def apply_preset(s=sugg):
                            name_input.value = s['name']
                            desc_input.value = s['desc']
                            color_input.value = s['color']
                            update_preview()
                        ui.button(sugg['name'], on_click=apply_preset).props('unelevated size=sm').style(
                            f'background-color: {sugg["color"]}15; color: {sugg["color"]}; font-weight: 600; border-radius: 999px; text-transform: none; border: 1px solid {sugg["color"]}30; padding: 4px 12px; font-size: 0.75rem; min-height: unset; height: unset; cursor: pointer;'
                        )

            desc_input = ui.textarea('Description').classes('w-full mb-4').props('outlined dense color=primary')
            
            # Color selector
            ui.label('Badge Color').classes('text-xs text-gray-500 mb-1')
            with ui.row().classes('w-full items-center gap-4 mb-6'):
                color_preview = ui.element('div').classes('w-12 h-8 rounded-md border border-slate-300')
                color_input = ui.input(placeholder='#ffffff').classes('flex-1').props('outlined dense color=primary')
                
                # Preset colors row
                presets = ['#10b981', '#3b82f6', '#eab308', '#ef4444', '#8b5cf6', '#6b7280']
                with ui.row().classes('gap-2 items-center'):
                    for p_color in presets:
                        def make_color_setter(color=p_color):
                            return lambda: set_color_value(color)
                        ui.element('div').on('click', make_color_setter()).style(
                            f'background-color: {p_color}; width: 24px; height: 24px; border-radius: 999px; cursor: pointer; border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.15); transition: transform 0.1s;'
                        ).classes('hover:scale-110')

            def update_preview():
                color_preview.style(f'background-color: {color_input.value or "#6b7280"}')

            color_input.on('change', update_preview)
            color_input.on('keyup', update_preview)

            def set_color_value(color_hex):
                color_input.value = color_hex
                update_preview()

            current_edit_record_id = [None]

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat color=primary')
                save_btn = ui.button('Save').classes('bg-primary text-white')

            save_btn.on('click', lambda: save_record(current_edit_record_id[0]))

        def open_dialog(record=None):
            if record:
                dialog_title.text = 'Edit Status'
                name_input.value = record['name']
                name_input.props('disable')  # Name is key
                desc_input.value = record['description']
                color_input.value = record['color']
                current_edit_record_id[0] = record['id']
            else:
                dialog_title.text = 'Create Status'
                name_input.value = ''
                name_input.props(remove='disable')
                desc_input.value = ''
                color_input.value = '#6b7280'
                current_edit_record_id[0] = None
            
            update_preview()
            dialog.open()

        def save_record(record_id):
            name = (name_input.value or '').strip()
            desc = (desc_input.value or '').strip()
            color = (color_input.value or '').strip() or '#6b7280'

            if not name:
                ui.notify('Status Name is required', type='warning')
                return

            db = SessionLocal()
            try:
                if record_id:
                    # Update (delete then re-add, or update description/color)
                    # For simplicity, we delete status first if it was changed, or we just call add/delete
                    if status_type == 'task':
                        StatusController.delete_task_status(db, record_id)
                        res = StatusController.add_task_status(db, name, desc, color)
                    else:
                        StatusController.delete_employee_status(db, record_id)
                        res = StatusController.add_employee_status(db, name, desc, color)
                else:
                    if status_type == 'task':
                        res = StatusController.add_task_status(db, name, desc, color)
                    else:
                        res = StatusController.add_employee_status(db, name, desc, color)
                
                if res["success"]:
                    ui.notify('Status saved successfully', type='positive')
                    dialog.close()
                    filter_records()
                else:
                    ui.notify(res["message"], type='warning')
            except Exception as e:
                db.rollback()
                ui.notify(f'Error saving status: {str(e)}', type='negative')
            finally:
                db.close()

        selected_record_id = [None]

        # Delete confirmation dialog
        delete_dialog = ui.dialog()
        with delete_dialog, ui.card().classes('p-6 glass-card'):
            ui.label('Are you sure you want to delete this status?').classes('text-lg font-bold mb-4 text-slate-800')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=delete_dialog.close).props('flat color=primary')
                confirm_delete_btn = ui.button('Delete', color='negative')

        def confirm_delete():
            record_id = selected_record_id[0]
            if record_id is None:
                return
            db = SessionLocal()
            try:
                if status_type == 'task':
                    res = StatusController.delete_task_status(db, record_id)
                else:
                    res = StatusController.delete_employee_status(db, record_id)
                if res["success"]:
                    ui.notify('Status deleted successfully', type='positive')
                else:
                    ui.notify(res["message"], type='warning')
                delete_dialog.close()
                filter_records()
            except Exception as e:
                db.rollback()
                ui.notify(f'Error deleting status: {str(e)}', type='negative')
            finally:
                db.close()

        confirm_delete_btn.on('click', confirm_delete)

        def open_delete_modal(record):
            selected_record_id[0] = record['id']
            delete_dialog.open()

        table.on('edit_record', lambda msg: open_dialog(msg.args))
        table.on('delete_record', lambda msg: open_delete_modal(msg.args))


@ui.page('/admin/masters/task-statuses')
def manage_task_statuses():
    render_master_page(
        status_type='task',
        page_title='Task Status Master',
        page_subtitle='Manage statuses available for employee tasks',
        active_route='/admin/masters/task-statuses'
    )

@ui.page('/admin/masters/employee-statuses')
def manage_employee_statuses():
    render_master_page(
        status_type='employee',
        page_title='Employee Status Master',
        page_subtitle='Manage statuses available for employees',
        active_route='/admin/masters/employee-statuses'
    )
