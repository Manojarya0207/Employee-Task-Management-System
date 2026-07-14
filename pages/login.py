from nicegui import app, ui
from models import SessionLocal
from services.auth_service import authenticate_user

def init_login_routes():
    @ui.page('/login')
    def login_page():
        # Check if already authenticated
        if app.storage.user.get('authenticated', False):
            role = app.storage.user.get('role', 'employee')
            ui.navigate.to('/admin' if role == 'admin' else '/employee')
            return
            
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

        # Centered container
        with ui.element('div').classes('w-full min-h-screen flex items-center justify-center p-4'):
            # Login Card (Glassmorphic)
            with ui.element('div').classes('glass-card p-8 w-full max-w-md'):
                
                # Brand Header
                with ui.element('div').classes('flex flex-col items-center mb-8'):
                    ui.element('i').classes('ri-rocket-fill text-primary text-5xl mb-2')
                    ui.label('TASKFLOW').classes('font-extrabold text-2xl tracking-wider brand-title')
                    ui.label('Employee Task Management System').classes('text-gray-500 text-xs mt-1 text-center')
                
                # Input fields
                employee_id_input = ui.input(label='Employee ID').classes('w-full mb-4').props('outlined color=primary')
                password_input = ui.input(label='Password', password=True).classes('w-full mb-6').props('outlined color=primary').on('keydown.enter', lambda: try_login())
                
                def try_login():
                    emp_id = employee_id_input.value
                    pwd = password_input.value
                    
                    if not emp_id or not pwd:
                        ui.notify('Please enter both Employee ID and Password', type='warning')
                        return
                        
                    db = SessionLocal()
                    try:
                        success, employee, message = authenticate_user(db, emp_id, pwd)
                        if success and employee:
                            # Set user session storage
                            app.storage.user.update({
                                'employee_id': employee.employee_id,
                                'employee_name': employee.employee_name,
                                'role': employee.role,
                                'authenticated': True
                            })
                            ui.notify(f"Welcome back, {employee.employee_name}!", type='positive')
                            
                            # Enforce change password reminder if default admin pwd matches
                            if employee.employee_id == 'admin' and pwd == 'Admin@123':
                                ui.notify('SECURITY WARNING: Please change your default password immediately!', type='negative', duration=10)
                                
                            ui.navigate.to('/admin' if employee.role == 'admin' else '/employee')
                        else:
                            ui.notify(message, type='negative')
                    finally:
                        db.close()

                # Action button
                ui.button('Sign In', on_click=try_login).classes('w-full py-3 text-base btn-neon').props('unelevated')
