from nicegui import app, ui
from models import SessionLocal
from services.registration_service import count_pending_requests

def toggle_submenu(submenu, chevron):
    visible = not submenu.visible
    submenu.set_visibility(visible)
    chevron.classes(replace='ri-arrow-up-s-line text-base ml-auto' if visible else 'ri-arrow-down-s-line text-base ml-auto')

def do_logout():
    app.storage.user.clear()
    ui.notify('Logged out successfully', type='positive')
    ui.navigate.to('/login')

def render_layout(active_route: str, action: str = None):
    """
    Renders the common sidebar layout and wraps page content.
    Returns the page container to append components to.
    """
    # Set theme colors for NiceGUI/Quasar matching the industrial UI system
    ui.colors(primary='#0f766e', secondary='#111827', accent='#14b8a6')
    ui.add_head_html('<link rel="stylesheet" href="/static/css/custom.css">')
    ui.add_head_html('<link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">')
    ui.add_head_html('''
        <script>
            window.addEventListener('click', (event) => {
                const button = event.target.closest('.btn-neon');
                if (button && !button.classList.contains('is-loading')) {
                    button.classList.add('is-loading');
                    window.setTimeout(() => button.classList.remove('is-loading'), 900);
                }
                
            });
            function closeMobileSidebar() {
                const sidebar = document.querySelector('.sidebar');
                const backdrop = document.querySelector('.sidebar-backdrop');
                if (sidebar) sidebar.classList.remove('mobile-open');
                if (backdrop) backdrop.classList.remove('visible');
            }
            function toggleMobileSidebar() {
                const sidebar = document.querySelector('.sidebar');
                const backdrop = document.querySelector('.sidebar-backdrop');
                if (sidebar) {
                    sidebar.classList.toggle('mobile-open');
                    if (backdrop) backdrop.classList.toggle('visible', sidebar.classList.contains('mobile-open'));
                }
            }
            window.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') closeMobileSidebar();
            });
        </script>
    ''')

    user_name = app.storage.user.get('employee_name', 'User')
    user_role = app.storage.user.get('role', 'employee')

    # Mobile Top Bar
    with ui.row().classes('mobile-topbar w-full items-center justify-between p-4 bg-white border-b border-slate-200'):
        with ui.row().classes('items-center gap-3'):
            with ui.button(on_click=lambda: ui.run_javascript('toggleMobileSidebar()')).props('flat round color=primary'):
                ui.element('i').classes('ri-menu-line text-2xl')
            ui.label('TASKFLOW').classes('font-extrabold text-lg tracking-wider text-slate-800')
        ui.label(user_name).classes('text-xs font-semibold text-slate-600')

    ui.element('div').classes('sidebar-backdrop').on('click', lambda: ui.run_javascript('closeMobileSidebar()'))

    # 1. Sidebar Container
    with ui.element('div').classes('sidebar'):
        # Brand Header
        with ui.element('div').classes('sidebar-brand'):
            ui.element('i').classes('ri-rocket-fill text-primary text-3xl')
            ui.label('TASKFLOW').classes('font-extrabold text-xl tracking-wider brand-title')
            with ui.button(on_click=lambda: ui.run_javascript('closeMobileSidebar()')).classes('sidebar-close-button').props('flat round dense aria-label="Close navigation"'):
                ui.element('i').classes('ri-close-line text-xl')

        # User Info Panel
        with ui.element('div').classes('user-panel mb-6 p-4 rounded-xl bg-slate-50 border border-slate-100'):
            ui.label(user_name).classes('user-name font-semibold text-sm truncate')
            ui.label(user_role.upper()).classes('user-role text-xs text-primary font-bold tracking-wider mt-1')

        # Navigation Menu Items
        with ui.element('div').classes('sidebar-menu'):
            if user_role == 'admin':
                # Fetch pending registration count for the sidebar badge
                try:
                    _db = SessionLocal()
                    _pending = count_pending_requests(_db)
                    _db.close()
                except Exception:
                    _pending = 0

                # 1. Dashboard
                active_class = 'active' if active_route == '/admin' else ''
                with ui.element('div').classes(f'menu-item {active_class}').on('click', lambda: ui.navigate.to('/admin')):
                    ui.element('i').classes('ri-dashboard-3-line text-lg')
                    ui.label('Dashboard').classes('text-sm font-medium flex-1')

                # 1.5. Daily Tasks
                daily_active = 'active' if active_route == '/admin/daily-tasks' else ''
                with ui.element('div').classes(f'menu-item {daily_active}').on('click', lambda: ui.navigate.to('/admin/daily-tasks')):
                    ui.element('i').classes('ri-calendar-todo-line text-lg')
                    ui.label('Daily Tasks').classes('text-sm font-medium flex-1')

                # 2. Employees Section (Collapsible)
                emp_expanded = active_route == '/admin/employees'
                
                with ui.element('div').classes('w-full') as emp_container:
                    with ui.element('div').classes('menu-parent').classes('expanded' if emp_expanded else '') as emp_header:
                        ui.element('i').classes('ri-group-line text-lg')
                        ui.label('Employees').classes('text-sm font-medium flex-1')
                        if _pending > 0:
                            ui.html(
                                f'<span style="'
                                f'background:#ef4444;color:white;border-radius:999px;'
                                f'font-size:0.65rem;font-weight:700;padding:1px 7px;'
                                f'min-width:20px;text-align:center;line-height:18px;'
                                f'display:inline-block;margin-right:8px">{_pending}</span>'
                            )
                        chevron_icon = 'ri-arrow-up-s-line' if emp_expanded else 'ri-arrow-down-s-line'
                        chevron = ui.element('i').classes(f'{chevron_icon} text-base ml-auto')
                    
                    emp_submenu = ui.element('div').classes('submenu-container')
                    emp_submenu.set_visibility(emp_expanded)

                    with emp_submenu:
                        # Employee List sub-menu item
                        list_active = 'active' if (active_route == '/admin/employees' and action != 'add') else ''
                        with ui.element('div').classes(f'submenu-item {list_active}').on('click', lambda: ui.navigate.to('/admin/employees')):
                            ui.element('i').classes('ri-list-check text-base')
                            ui.label('Employee List').classes('text-xs font-medium flex-1')
                            
                        # Add Employees sub-menu item
                        add_active = 'active' if (active_route == '/admin/employees' and action == 'add') else ''
                        with ui.element('div').classes(f'submenu-item {add_active}').on('click', lambda: ui.navigate.to('/admin/employees?action=add')):
                            ui.element('i').classes('ri-user-add-line text-base')
                            ui.label('Add Employees').classes('text-xs font-medium flex-1')
                    
                    emp_header.on('click', lambda: toggle_submenu(emp_submenu, chevron))

                # 3. Masters Section (Collapsible)
                masters_expanded = active_route.startswith('/admin/masters')
                
                with ui.element('div').classes('w-full') as masters_container:
                    with ui.element('div').classes('menu-parent').classes('expanded' if masters_expanded else '') as masters_header:
                        ui.element('i').classes('ri-shield-user-line text-lg')
                        ui.label('Masters').classes('text-sm font-medium flex-1')
                        chevron_icon = 'ri-arrow-up-s-line' if masters_expanded else 'ri-arrow-down-s-line'
                        chevron = ui.element('i').classes(f'{chevron_icon} text-base ml-auto')
                    
                    submenu = ui.element('div').classes('submenu-container')
                    submenu.set_visibility(masters_expanded)

                    with submenu:
                        # Task Statuses master sub-menu item
                        task_status_active = 'active' if active_route == '/admin/masters/task-statuses' else ''
                        with ui.element('div').classes(f'submenu-item {task_status_active}').on('click', lambda: ui.navigate.to('/admin/masters/task-statuses')):
                            ui.element('i').classes('ri-checkbox-multiple-line text-base')
                            ui.label('Task Statuses').classes('text-xs font-medium flex-1')

                        # Employee Statuses master sub-menu item
                        emp_status_active = 'active' if active_route == '/admin/masters/employee-statuses' else ''
                        with ui.element('div').classes(f'submenu-item {emp_status_active}').on('click', lambda: ui.navigate.to('/admin/masters/employee-statuses')):
                            ui.element('i').classes('ri-user-settings-line text-base')
                            ui.label('Employee Statuses').classes('text-xs font-medium flex-1')
                    
                    masters_header.on('click', lambda: toggle_submenu(submenu, chevron))

                # 3. Reports
                rep_active = 'active' if active_route == '/admin/reports' else ''
                with ui.element('div').classes(f'menu-item {rep_active}').on('click', lambda: ui.navigate.to('/admin/reports')):
                    ui.element('i').classes('ri-file-chart-line text-lg')
                    ui.label('Reports').classes('text-sm font-medium flex-1')

            else:
                routes = [
                    ('/employee',          'ri-home-4-line',          'My Dashboard',    None),
                    ('/employee/history',  'ri-calendar-todo-line',   'Tasks & Calendar', None),
                    ('/employee/profile',  'ri-user-settings-line',   'My Profile',      None),
                ]

                for path, icon, name, badge in routes:
                    active_class = 'active' if active_route == path else ''
                    with ui.element('div').classes(f'menu-item {active_class}').on('click', lambda p=path: ui.navigate.to(p)):
                        ui.element('i').classes(f'{icon} text-lg')
                        ui.label(name).classes('text-sm font-medium flex-1')

        # Logout Panel
        with ui.element('div').classes('mt-auto pt-4 border-t border-slate-200'):
            with ui.element('div').classes('menu-item hover:text-red-600').on('click', do_logout):
                ui.element('i').classes('ri-logout-box-r-line text-lg')
                ui.label('Logout').classes('text-sm')

    # 2. Main Wrapper
    main_cont = ui.element('div').classes('main-wrapper animated-fade')
    return main_cont
