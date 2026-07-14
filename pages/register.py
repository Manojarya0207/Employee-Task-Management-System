"""
pages/register.py

Self-service Employee Registration page at /register.

Features
--------
- Auto-generated Employee ID (live, read-only) from name + phone
- Live field validation with visual feedback
- Register button enabled only when all fields are valid
- On success: shows confirmation message and navigates back to /login
"""

from nicegui import app, ui
from models import SessionLocal
from models.employee import Employee
from services.registration_service import (
    generate_employee_id,
    generate_unique_employee_id,
    register_employee,
)
import re


def init_registration_routes():

    @ui.page('/register')
    def register_page():
        # Redirect if already logged in
        if app.storage.user.get('authenticated', False):
            role = app.storage.user.get('role', 'employee')
            ui.navigate.to('/admin' if role == 'admin' else '/employee')
            return

        ui.colors(primary='#0f766e', secondary='#111827', accent='#14b8a6')
        ui.add_head_html('<link rel="stylesheet" href="/static/css/custom.css">')
        ui.add_head_html('<link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">')
        ui.add_head_html('''
            <style>
                .reg-field-error  { border-color: #ef4444 !important; }
                .reg-field-ok     { border-color: #10b981 !important; }
                .hint-text        { font-size: 0.72rem; margin-top: 2px; min-height: 1.1rem; }
                .hint-error       { color: #ef4444; }
                .hint-ok          { color: #10b981; }
                .hint-neutral     { color: #94a3b8; }
                .emp-id-badge     {
                    background: linear-gradient(135deg, #0f766e 0%, #2563eb 100%);
                    color: white;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-family: monospace;
                    font-size: 1.25rem;
                    font-weight: 700;
                    letter-spacing: 2px;
                    text-align: center;
                    min-height: 48px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .register-btn { transition: all 0.2s ease; }
                .register-btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .success-panel {
                    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
                    border: 1px solid #10b981;
                    border-radius: 12px;
                    padding: 24px;
                    text-align: center;
                }
            </style>
        ''')

        # ----------------------------------------------------------------
        # State
        # ----------------------------------------------------------------
        state = {
            'name_ok': False,
            'phone_ok': False,
            'dept_ok': False,
            'pwd_ok': False,
            'confirm_ok': False,
            'submitting': False,
        }

        # ----------------------------------------------------------------
        # Layout
        # ----------------------------------------------------------------
        with ui.element('div').classes('w-full min-h-screen flex items-center justify-center p-4'):
            with ui.element('div').classes('glass-card p-8 w-full max-w-lg'):

                # ── Brand Header ──────────────────────────────────────────
                with ui.element('div').classes('flex flex-col items-center mb-6'):
                    ui.element('i').classes('ri-user-add-fill text-primary text-5xl mb-2')
                    ui.label('TASKFLOW').classes('font-extrabold text-2xl tracking-wider brand-title')
                    ui.label('Employee Registration').classes('text-gray-500 text-sm mt-1')

                # ── Form Container ────────────────────────────────────────
                with ui.element('div').classes('w-full') as form_container:
                    # ── Name Field ────────────────────────────────────────────
                    ui.label('Employee Name *').classes('text-xs font-semibold text-slate-900 mb-1')
                    name_input = (
                        ui.input(placeholder='e.g. Manoj Arya')
                        .classes('w-full mb-1')
                        .props('outlined color=primary maxlength=100')
                    )
                    name_hint = ui.label('Minimum 3 characters required').classes('hint-text hint-neutral mb-3')

                    # ── Phone Field ───────────────────────────────────────────
                    ui.label('Phone Number *').classes('text-xs font-semibold text-slate-900 mb-1')
                    phone_input = (
                        ui.input(placeholder='10-digit mobile number')
                        .classes('w-full mb-1')
                        .props('outlined color=primary maxlength=10')
                    )
                    phone_hint = ui.label('Exactly 10 digits required').classes('hint-text hint-neutral mb-3')

                    # ── Department Field ──────────────────────────────────────
                    ui.label('Department / vertical *').classes('text-xs font-semibold text-slate-900 mb-1')
                    dept_select = (
                        ui.select(
                            options={
                                '': 'Select department',
                                'AI / ML': 'AI / ML',
                                'IoT': 'IoT',
                                'Robotics': 'Robotics',
                                'AR / VR': 'AR / VR',
                                'Others': 'Others'
                            },
                            value=''
                        )
                        .classes('w-full mb-1')
                        .props('outlined color=primary')
                    )
                    dept_hint = ui.label('Please select a department').classes('hint-text hint-neutral mb-3')

                    # ── Custom Department Field ──────────────────────────────
                    other_dept_label = ui.label('Specify Department *').classes('text-xs font-semibold text-slate-900 mb-1').bind_visibility_from(dept_select, 'value', value='Others')
                    other_dept_input = (
                        ui.input(placeholder='Enter your department')
                        .classes('w-full mb-1')
                        .props('outlined color=primary maxlength=100')
                        .bind_visibility_from(dept_select, 'value', value='Others')
                    )
                    other_dept_hint = ui.label('Minimum 2 characters required').classes('hint-text hint-neutral mb-3').bind_visibility_from(dept_select, 'value', value='Others')

                    # ── Auto-generated Employee ID ────────────────────────────
                    ui.label('Employee ID (Auto-Generated)').classes('text-xs font-semibold text-slate-900 mb-1')
                    with ui.element('div').classes('emp-id-badge mb-1') as emp_id_container:
                        emp_id_label = ui.label('—').classes('tracking-widest')
                    ui.label('Generated from your name and phone number').classes('hint-text hint-neutral mb-3')

                    # ── Password Field ────────────────────────────────────────
                    ui.label('Password *').classes('text-xs font-semibold text-slate-900 mb-1')
                    pwd_input = (
                        ui.input(placeholder='Minimum 8 characters', password=True, password_toggle_button=True)
                        .classes('w-full mb-1')
                        .props('outlined color=primary')
                    )
                    pwd_hint = ui.label('Minimum 8 characters required').classes('hint-text hint-neutral mb-3')

                    # ── Confirm Password Field ────────────────────────────────
                    ui.label('Confirm Password *').classes('text-xs font-semibold text-slate-900 mb-1')
                    confirm_input = (
                        ui.input(placeholder='Re-enter your password', password=True, password_toggle_button=True)
                        .classes('w-full mb-1')
                        .props('outlined color=primary')
                    )
                    confirm_hint = ui.label('Passwords must match').classes('hint-text hint-neutral mb-4')

                    # ── Register Button ───────────────────────────────────────
                    register_btn = (
                        ui.button('Create Registration Request', icon='how_to_reg')
                        .classes('w-full py-3 text-base btn-neon register-btn')
                        .props('unelevated disable')
                    )

                    with ui.element('div').classes('flex justify-center mt-4'):
                        ui.label('Already registered?').classes('text-gray-500 text-sm mr-1')
                        ui.link('Sign In', '/login').classes('text-primary text-sm font-semibold')

                # ----------------------------------------------------------------
                # Validation helpers
                # ----------------------------------------------------------------
                def update_btn():
                    all_ok = all(state[k] for k in ('name_ok', 'phone_ok', 'dept_ok', 'pwd_ok', 'confirm_ok'))
                    if all_ok:
                        register_btn.props(remove='disable')
                    else:
                        register_btn.props('disable')

                def refresh_emp_id():
                    name = name_input.value or ''
                    phone = phone_input.value or ''
                    # Only show ID when at least something meaningful is typed
                    if len(re.sub(r'[^a-zA-Z]', '', name)) > 0 or len(re.sub(r'\D', '', phone)) >= 4:
                        emp_id_label.set_text(generate_employee_id(name, phone) or '—')
                    else:
                        emp_id_label.set_text('—')

                def validate_name():
                    val = name_input.value or ''
                    if len(val.strip()) >= 3:
                        state['name_ok'] = True
                        name_hint.set_text('✓ Looks good!')
                        name_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                    else:
                        state['name_ok'] = False
                        remain = 3 - len(val.strip())
                        name_hint.set_text(f'{remain} more character(s) needed')
                        name_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                    refresh_emp_id()
                    validate_confirm()  # re-check confirm if pwd changed
                    update_btn()

                def validate_phone():
                    val = re.sub(r'\D', '', phone_input.value or '')
                    if len(val) == 10:
                        db = SessionLocal()
                        try:
                            phone_exists = db.query(Employee).filter(Employee.phone_number == val).first()
                            if phone_exists:
                                state['phone_ok'] = False
                                phone_hint.set_text('✗ Phone number is already registered')
                                phone_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                            else:
                                state['phone_ok'] = True
                                phone_hint.set_text('✓ Valid phone number')
                                phone_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                        finally:
                            db.close()
                    else:
                        state['phone_ok'] = False
                        remain = 10 - len(val)
                        phone_hint.set_text(f'{remain} more digit(s) needed')
                        phone_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                    refresh_emp_id()
                    update_btn()

                def validate_password():
                    val = pwd_input.value or ''
                    if len(val) >= 8:
                        state['pwd_ok'] = True
                        pwd_hint.set_text('✓ Strong enough!')
                        pwd_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                    else:
                        state['pwd_ok'] = False
                        remain = 8 - len(val)
                        pwd_hint.set_text(f'{remain} more character(s) needed')
                        pwd_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                    validate_confirm()
                    update_btn()

                def validate_confirm():
                    p = pwd_input.value or ''
                    c = confirm_input.value or ''
                    if c and p == c:
                        state['confirm_ok'] = True
                        confirm_hint.set_text('✓ Passwords match')
                        confirm_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                    else:
                        state['confirm_ok'] = False
                        if c:
                            confirm_hint.set_text('✗ Passwords do not match')
                            confirm_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                        else:
                            confirm_hint.set_text('Passwords must match')
                            confirm_hint.classes(remove='hint-ok hint-error', add='hint-neutral')
                    update_btn()

                def validate_dept():
                    val = dept_select.value or ''
                    if val == 'Others':
                        other_val = (other_dept_input.value or '').strip()
                        if len(other_val) >= 2:
                            state['dept_ok'] = True
                            other_dept_hint.set_text('✓ Looks good!')
                            other_dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                        else:
                            state['dept_ok'] = False
                            other_dept_hint.set_text('Minimum 2 characters required')
                            other_dept_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                        dept_hint.set_text('✓ Custom department selected')
                        dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                    elif val != '':
                        state['dept_ok'] = True
                        dept_hint.set_text('✓ Looks good!')
                        dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
                    else:
                        state['dept_ok'] = False
                        dept_hint.set_text('Please select a department')
                        dept_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                    update_btn()



                # ----------------------------------------------------------------
                # Registration submission
                # ----------------------------------------------------------------
                async def do_register():
                    import asyncio
                    if state['submitting']:
                        return
                    state['submitting'] = True
                    register_btn.props('loading disable')

                    db = SessionLocal()
                    try:
                        success, message, emp_id = register_employee(
                            db=db,
                            employee_name=name_input.value.strip(),
                            phone_number=phone_input.value.strip(),
                            password=pwd_input.value,
                            department=other_dept_input.value.strip() if dept_select.value == 'Others' else dept_select.value,
                        )

                        if success:
                            # Show success panel, hide entire form container
                            form_container.set_visibility(False)

                            # Hide field titles by class (can't easily target; use notification + inline panel)
                            ui.notify(
                                'Registration submitted! Awaiting admin approval.',
                                type='positive',
                                duration=6000,
                             )

                            with ui.element('div').classes('success-panel mt-2'):
                                ui.element('i').classes('ri-checkbox-circle-fill text-emerald-400 text-5xl mb-3')
                                ui.label('Registration Submitted!').classes('text-white text-xl font-bold mb-2')
                                ui.label(
                                    f'Your Employee ID is: {emp_id}'
                                ).classes('text-emerald-300 font-mono text-lg font-bold mb-3')
                                ui.label(
                                    'Your account is pending administrator approval. '
                                    'You will be able to log in once your request is reviewed.'
                                ).classes('text-gray-300 text-sm leading-relaxed mb-4')
                                ui.button('Back to Login', icon='login', on_click=lambda: ui.navigate.to('/login'))\
                                    .classes('btn-neon w-full')
                                redirect_label = ui.label('Redirecting to Login in 5 seconds...').classes('text-emerald-400/80 text-xs mt-3')

                            for seconds_left in range(5, 0, -1):
                                redirect_label.set_text(f'Redirecting to Login in {seconds_left} seconds...')
                                await asyncio.sleep(1)
                            ui.navigate.to('/login')

                        else:
                            ui.notify(message, type='negative', duration=5000)
                            state['submitting'] = False
                            register_btn.props(remove='loading')
                            register_btn.props(remove='disable')

                    except Exception as exc:
                        ui.notify(f'Unexpected error: {str(exc)}', type='negative')
                        state['submitting'] = False
                        register_btn.props(remove='loading')
                    finally:
                        db.close()

                register_btn.on('click', do_register)

                # Bind events
                name_input.on_value_change(lambda: validate_name())
                phone_input.on_value_change(lambda: validate_phone())
                dept_select.on_value_change(lambda: validate_dept())
                other_dept_input.on_value_change(lambda: validate_dept())
                pwd_input.on_value_change(lambda: validate_password())
                confirm_input.on_value_change(lambda: validate_confirm())
                confirm_input.on('keydown.enter', do_register)
