from nicegui import app, ui

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
                # Admin routes
                routes = [
                    ('/admin', 'ri-dashboard-3-line', 'Dashboard'),
                    ('/admin/employees', 'ri-group-line', 'Employees'),
                    ('/admin/tasks', 'ri-task-line', 'Employee Tasks'),
                    ('/admin/reports', 'ri-file-chart-line', 'Reports'),
                ]
            else:
                # Employee routes
                routes = [
                    ('/employee', 'ri-home-4-line', 'My Dashboard'),
                    ('/employee/history', 'ri-calendar-todo-line', 'Tasks & Calendar'),
                    ('/employee/profile', 'ri-user-settings-line', 'My Profile'),
                ]
                
            for path, icon, name in routes:
                active_class = 'active' if active_route == path else ''
                with ui.element('div').classes(f'menu-item {active_class}').on('click', lambda p=path: ui.navigate.to(p)):
                    ui.element('i').classes(f'{icon} text-lg')
                    ui.label(name).classes('text-sm font-medium')
                    
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
