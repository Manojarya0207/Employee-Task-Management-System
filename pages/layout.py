from nicegui import app, ui
from models import SessionLocal
from services.registration_service import count_pending_requests


def render_layout(active_route: str):
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
                if (!button || button.classList.contains('is-loading')) return;
                button.classList.add('is-loading');
                window.setTimeout(() => button.classList.remove('is-loading'), 900);
            });
        </script>
    ''')

    user_name = app.storage.user.get('employee_name', 'User')
    user_role = app.storage.user.get('role', 'employee')

    # 1. Sidebar Container
    with ui.element('div').classes('sidebar'):
        # Brand Header
        with ui.element('div').classes('sidebar-brand'):
            ui.element('i').classes('ri-rocket-fill text-primary text-3xl')
            ui.label('TASKFLOW').classes('font-extrabold text-xl tracking-wider brand-title')

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

                # 2. Masters Section (Collapsible)
                masters_expanded = active_route in ('/admin/employees', '/admin/tasks')
                
                with ui.element('div').classes('w-full') as masters_container:
                    with ui.element('div').classes('menu-parent').classes('expanded' if masters_expanded else '') as masters_header:
                        ui.element('i').classes('ri-shield-user-line text-lg')
                        ui.label('Masters').classes('text-sm font-medium flex-1')
                        chevron_icon = 'ri-arrow-up-s-line' if masters_expanded else 'ri-arrow-down-s-line'
                        chevron = ui.element('i').classes(f'{chevron_icon} text-base ml-auto')
                    
                    submenu = ui.element('div').classes('submenu-container')
                    submenu.set_visibility(masters_expanded)

                    # Employees sub-menu item
                    emp_active = 'active' if active_route == '/admin/employees' else ''
                    with submenu:
                        with ui.element('div').classes(f'submenu-item {emp_active}').on('click', lambda: ui.navigate.to('/admin/employees')):
                            ui.element('i').classes('ri-group-line text-base')
                            ui.label('Employees').classes('text-xs font-medium flex-1')
                            if _pending > 0:
                                ui.html(
                                    f'<span style="'
                                    f'background:#ef4444;color:white;border-radius:999px;'
                                    f'font-size:0.65rem;font-weight:700;padding:1px 7px;'
                                    f'min-width:20px;text-align:center;line-height:18px;'
                                    f'display:inline-block;margin-left:auto">{_pending}</span>'
                                )
                        
                        # Employee Tasks Status sub-menu item
                        task_active = 'active' if active_route == '/admin/tasks' else ''
                        with ui.element('div').classes(f'submenu-item {task_active}').on('click', lambda: ui.navigate.to('/admin/tasks')):
                            ui.element('i').classes('ri-task-line text-base')
                            ui.label('Employee Tasks Status').classes('text-xs font-medium flex-1')

                    def toggle():
                        visible = not submenu.visible
                        submenu.set_visibility(visible)
                        chevron.classes(replace='ri-arrow-up-s-line text-base ml-auto' if visible else 'ri-arrow-down-s-line text-base ml-auto')
                    
                    masters_header.on('click', toggle)

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
            def do_logout():
                app.storage.user.clear()
                ui.notify('Logged out successfully', type='positive')
                ui.navigate.to('/login')

            with ui.element('div').classes('menu-item hover:text-red-600').on('click', do_logout):
                ui.element('i').classes('ri-logout-box-r-line text-lg')
                ui.label('Logout').classes('text-sm')

    # 2. Main Wrapper
    main_cont = ui.element('div').classes('main-wrapper animated-fade')
    return main_cont
