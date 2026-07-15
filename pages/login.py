from nicegui import app, ui
from models import SessionLocal
from models.employee import Employee
from services.auth_service import authenticate_user

# Helper functions to reduce login_page complexity
def perform_login(employee_id_input, password_input, show_status_view):
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
            # Support multi-line messages (e.g. rejection reason)
            display_msg = message.replace('\n', '<br>') if '\n' in message else message
            ui.notify(display_msg, type='negative', html=True, duration=7000)
            
            # Show status view if registration status is pending or rejected
            if employee_id_input.value:
                db_check = SessionLocal()
                try:
                    emp = db_check.query(Employee).filter(Employee.employee_id == employee_id_input.value).first()
                    if emp and getattr(emp, 'registration_status', 'approved') in ('pending', 'rejected'):
                        show_status_view(employee_id_input.value)
                finally:
                    db_check.close()
    finally:
        db.close()

def check_registration_status(status_id_input, details_container):
    id_to_check = status_id_input.value
    if not id_to_check:
        ui.notify('Please enter an Employee ID', type='warning')
        return
    
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.employee_id == id_to_check).first()
        details_container.classes(remove='hidden')
        details_container.clear()
        with details_container:
            if not employee:
                ui.label('No employee found with this ID.').classes('text-red-400 font-semibold text-sm')
            else:
                status = getattr(employee, 'registration_status', 'approved')
                ui.label(f"Employee: {employee.employee_name}").classes('text-white font-semibold text-sm mb-1')
                
                if status == 'pending':
                    ui.label('Status: PENDING APPROVAL').classes('text-amber-400 font-bold text-sm mb-2')
                    ui.label('Your request is waiting for administrator approval. You will be able to sign in once approved.').classes('text-gray-300 text-xs leading-relaxed')
                elif status == 'rejected':
                    ui.label('Status: REJECTED').classes('text-red-400 font-bold text-sm mb-1')
                    reason = getattr(employee, 'rejection_reason', None)
                    if reason:
                        ui.label(f"Reason: {reason}").classes('text-red-300 text-xs font-semibold mb-2 bg-red-950/50 p-2 rounded leading-relaxed')
                    else:
                        ui.label('Your registration request was rejected. Please contact an admin.').classes('text-gray-300 text-xs leading-relaxed')
                else:
                    ui.label('Status: APPROVED / ACTIVE').classes('text-emerald-400 font-bold text-sm mb-2')
                    ui.label('Your account is fully approved. You can sign in using your password.').classes('text-gray-300 text-xs leading-relaxed')
    finally:
        db.close()


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
            
            # Login form container
            form_container = ui.element('div').classes('w-full')
            
            # Status check container (hidden by default)
            status_container = ui.element('div').classes('w-full hidden')
            
            with form_container:
                # Input fields
                employee_id_input = ui.input(label='Employee ID').classes('w-full mb-4').props('outlined color=primary')
                
                # We define this helper dynamically to close over current layout containers
                def show_status_view(emp_id=None):
                    form_container.classes('hidden')
                    status_container.classes(remove='hidden')
                    target_id = emp_id or employee_id_input.value or ''
                    status_id_input.value = target_id
                    if target_id:
                        check_registration_status(status_id_input, details_container)

                password_input = ui.input(label='Password', password=True, password_toggle_button=True).classes('w-full mb-6').props('outlined color=primary').on('keydown.enter', lambda: perform_login(employee_id_input, password_input, show_status_view))
                
                # Action button
                ui.button('Sign In', on_click=lambda: perform_login(employee_id_input, password_input, show_status_view)).classes('w-full py-3 text-base btn-neon').props('unelevated')
                
                # Register link & Check Status link
                with ui.element('div').classes('flex flex-col items-center mt-5 gap-2'):
                    with ui.element('div').classes('flex justify-center items-center gap-1'):
                        ui.label("New employee?").classes('text-gray-500 text-sm')
                        ui.link('Register here →', '/register').classes('text-primary text-sm font-semibold hover:underline')
                    ui.button('Check Registration Status', on_click=lambda: show_status_view()).classes('text-xs text-slate-400 hover:text-white cursor-pointer mt-1').props('flat dense')

            with status_container:
                ui.label('Registration Status').classes('text-lg font-bold mb-4 text-center text-white')
                status_id_input = ui.input(label='Employee ID').classes('w-full mb-4').props('outlined color=primary')
                
                details_container = ui.element('div').classes('w-full mb-4 p-4 rounded-lg bg-slate-800/80 border border-slate-700 hidden')
                
                ui.button('Check Status', on_click=lambda: check_registration_status(status_id_input, details_container)).classes('w-full py-2 mb-3 btn-neon').props('unelevated')
                
                def back_to_login():
                    status_container.classes('hidden')
                    form_container.classes(remove='hidden')
                    details_container.classes('hidden')
                    details_container.clear()
                    
                ui.button('Back to Login', on_click=back_to_login).classes('w-full py-2 text-gray-300 hover:text-white').props('flat icon=arrow_back')


def init_login_routes():
    pass
