from nicegui import app, ui
from models import SessionLocal
from models.employee import Employee
from services.registration_service import (
    generate_employee_id,
    generate_unique_employee_id,
    register_employee,
)
import re
import asyncio

PATH_LOGIN = '/login'
CLASS_SLATE_900_LABEL = 'text-xs font-semibold text-slate-900 mb-1'
CLASS_WFULL_MB1 = 'w-full mb-1'
CLASS_HINT_TEXT_MB3 = 'hint-text hint-neutral mb-3'

class RegistrationForm:
    def __init__(self):
        self.state = {
            'name_ok': False,
            'phone_ok': False,
            'dept_ok': False,
            'pwd_ok': False,
            'confirm_ok': False,
            'submitting': False,
        }

    def update_btn(self):
        all_ok = all(self.state[k] for k in ('name_ok', 'phone_ok', 'dept_ok', 'pwd_ok', 'confirm_ok'))
        if all_ok:
            self.register_btn.props(remove='disable')
        else:
            self.register_btn.props('disable')

    def refresh_emp_id(self):
        name = self.name_input.value or ''
        phone = self.phone_input.value or ''
        # Only show ID when at least something meaningful is typed
        if len(re.sub(r'[^a-zA-Z]', '', name)) > 0 or len(re.sub(r'\D', '', phone)) >= 4:
            self.emp_id_label.set_text(generate_employee_id(name, phone) or '—')
        else:
            self.emp_id_label.set_text('—')

    def validate_name(self):
        val = self.name_input.value or ''
        if len(val.strip()) >= 3:
            self.state['name_ok'] = True
            self.name_hint.set_text('✓ Looks good!')
            self.name_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
        else:
            self.state['name_ok'] = False
            remain = 3 - len(val.strip())
            self.name_hint.set_text(f'{remain} more character(s) needed')
            self.name_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
        self.refresh_emp_id()
        self.validate_confirm()  # re-check confirm if pwd changed
        self.update_btn()

    def validate_phone(self):
        val = re.sub(r'\D', '', self.phone_input.value or '')
        if len(val) == 10:
            db = SessionLocal()
            try:
                phone_exists = db.query(Employee).filter(Employee.phone_number == val).first()
                if phone_exists:
                    self.state['phone_ok'] = False
                    self.phone_hint.set_text('✗ Phone number is already registered')
                    self.phone_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
                else:
                    self.state['phone_ok'] = True
                    self.phone_hint.set_text('✓ Valid phone number')
                    self.phone_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
            finally:
                db.close()
        else:
            self.state['phone_ok'] = False
            remain = 10 - len(val)
            self.phone_hint.set_text(f'{remain} more digit(s) needed')
            self.phone_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
        self.refresh_emp_id()
        self.update_btn()

    def validate_password(self):
        val = self.pwd_input.value or ''
        if len(val) >= 6:
            self.state['pwd_ok'] = True
            self.pwd_hint.set_text('✓ Strong enough!')
            self.pwd_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
        else:
            self.state['pwd_ok'] = False
            remain = 6 - len(val)
            self.pwd_hint.set_text(f'{remain} more character(s) needed')
            self.pwd_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
        self.validate_confirm()
        self.update_btn()

    def validate_confirm(self):
        p = self.pwd_input.value or ''
        c = self.confirm_input.value or ''
        if c and p == c:
            self.state['confirm_ok'] = True
            self.confirm_hint.set_text('✓ Passwords match')
            self.confirm_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
        else:
            self.state['confirm_ok'] = False
            if c:
                self.confirm_hint.set_text('✗ Passwords do not match')
                self.confirm_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
            else:
                self.confirm_hint.set_text('Passwords must match')
                self.confirm_hint.classes(remove='hint-ok hint-error', add='hint-neutral')
        self.update_btn()

    def validate_dept(self):
        val = self.dept_select.value or ''
        if val == 'Others':
            other_val = (self.other_dept_input.value or '').strip()
            if len(other_val) >= 2:
                self.state['dept_ok'] = True
                self.other_dept_hint.set_text('✓ Looks good!')
                self.other_dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
            else:
                self.state['dept_ok'] = False
                self.other_dept_hint.set_text('Minimum 2 characters required')
                self.other_dept_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
            self.dept_hint.set_text('✓ Custom department selected')
            self.dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
        elif val != '':
            self.state['dept_ok'] = True
            self.dept_hint.set_text('✓ Looks good!')
            self.dept_hint.classes(remove='hint-error hint-neutral', add='hint-ok')
        else:
            self.state['dept_ok'] = False
            self.dept_hint.set_text('Please select a department')
            self.dept_hint.classes(remove='hint-ok hint-neutral', add='hint-error')
        self.update_btn()

    async def do_register(self):
        if self.state['submitting']:
            return
        self.state['submitting'] = True
        self.register_btn.props('loading disable')

        db = SessionLocal()
        try:
            success, message, emp_id = register_employee(
                db=db,
                employee_name=self.name_input.value.strip(),
                phone_number=self.phone_input.value.strip(),
                password=self.pwd_input.value,
                department=self.other_dept_input.value.strip() if self.dept_select.value == 'Others' else self.dept_select.value,
            )

            if success:
                self.form_container.set_visibility(False)

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
                self.state['submitting'] = False
                self.register_btn.props(remove='loading')
                self.register_btn.props(remove='disable')

        except Exception as exc:
            ui.notify(f'Unexpected error: {str(exc)}', type='negative')
            self.state['submitting'] = False
            self.register_btn.props(remove='loading')
        finally:
            db.close()

    def build(self):
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

        with ui.element('div').classes('w-full min-h-screen flex items-center justify-center p-4'):
            with ui.element('div').classes('glass-card p-8 w-full max-w-lg'):

                # ── Brand Header ──────────────────────────────────────────
                with ui.element('div').classes('flex flex-col items-center mb-6'):
                    ui.element('i').classes('ri-user-add-fill text-primary text-5xl mb-2')
                    ui.label('TASKFLOW').classes('font-extrabold text-2xl tracking-wider brand-title')
                    ui.label('Employee Registration').classes('text-gray-500 text-sm mt-1')

                # ── Form Container ────────────────────────────────────────
                self.form_container = ui.element('div').classes('w-full')
                with self.form_container:
                    # ── Name Field ────────────────────────────────────────────
                    ui.label('Employee Name *').classes(CLASS_SLATE_900_LABEL)
                    self.name_input = (
                        ui.input(placeholder='e.g. Manoj Arya')
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary maxlength=100')
                    )
                    self.name_hint = ui.label('Minimum 3 characters required').classes(CLASS_HINT_TEXT_MB3)

                    # ── Phone Field ───────────────────────────────────────────
                    ui.label('Phone Number *').classes(CLASS_SLATE_900_LABEL)
                    self.phone_input = (
                        ui.input(placeholder='10-digit mobile number')
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary maxlength=10')
                    )
                    self.phone_hint = ui.label('Exactly 10 digits required').classes(CLASS_HINT_TEXT_MB3)

                    # ── Department Field ──────────────────────────────────────
                    ui.label('Department / vertical *').classes(CLASS_SLATE_900_LABEL)
                    self.dept_select = (
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
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary')
                    )
                    self.dept_hint = ui.label('Please select a department').classes(CLASS_HINT_TEXT_MB3)

                    # ── Custom Department Field ──────────────────────────────
                    other_dept_label = ui.label('Specify Department *').classes(CLASS_SLATE_900_LABEL).bind_visibility_from(self.dept_select, 'value', value='Others')
                    self.other_dept_input = (
                        ui.input(placeholder='Enter your department')
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary maxlength=100')
                        .bind_visibility_from(self.dept_select, 'value', value='Others')
                    )
                    self.other_dept_hint = ui.label('Minimum 2 characters required').classes(CLASS_HINT_TEXT_MB3).bind_visibility_from(self.dept_select, 'value', value='Others')

                    # ── Auto-generated Employee ID ────────────────────────────
                    ui.label('Employee ID (Auto-Generated)').classes(CLASS_SLATE_900_LABEL)
                    with ui.element('div').classes('emp-id-badge mb-1'):
                        self.emp_id_label = ui.label('—').classes('tracking-widest')
                    ui.label('Generated from your name and phone number').classes(CLASS_HINT_TEXT_MB3)

                    # ── Password Field ────────────────────────────────────────
                    ui.label('Password *').classes(CLASS_SLATE_900_LABEL)
                    self.pwd_input = (
                        ui.input(placeholder='Minimum 6 characters', password=True, password_toggle_button=True)
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary')
                    )
                    self.pwd_hint = ui.label('Minimum 6 characters required').classes(CLASS_HINT_TEXT_MB3)

                    # ── Confirm Password Field ────────────────────────────────
                    ui.label('Confirm Password *').classes(CLASS_SLATE_900_LABEL)
                    self.confirm_input = (
                        ui.input(placeholder='Re-enter your password', password=True, password_toggle_button=True)
                        .classes(CLASS_WFULL_MB1)
                        .props('outlined color=primary')
                    )
                    self.confirm_hint = ui.label('Passwords must match').classes('hint-text hint-neutral mb-4')

                    # ── Register Button ───────────────────────────────────────
                    self.register_btn = (
                        ui.button('Create Registration Request', icon='how_to_reg')
                        .classes('w-full py-3 text-base btn-neon register-btn')
                        .props('unelevated disable')
                    )

                    with ui.element('div').classes('flex justify-center mt-4'):
                        ui.label('Already registered?').classes('text-gray-500 text-sm mr-1')
                        ui.link('Sign In', PATH_LOGIN).classes('text-primary text-sm font-semibold')

                self.register_btn.on('click', lambda: self.do_register())

                # Bind events
                self.name_input.on_value_change(lambda: self.validate_name())
                self.phone_input.on_value_change(lambda: self.validate_phone())
                self.dept_select.on_value_change(lambda: self.validate_dept())
                self.other_dept_input.on_value_change(lambda: self.validate_dept())
                self.pwd_input.on_value_change(lambda: self.validate_password())
                self.confirm_input.on_value_change(lambda: self.validate_confirm())
                self.confirm_input.on('keydown.enter', lambda: self.do_register())


@ui.page('/register')
def register_page():
    # Redirect if already logged in
    if app.storage.user.get('authenticated', False):
        role = app.storage.user.get('role', 'employee')
        ui.navigate.to('/admin' if role == 'admin' else '/employee')
        return

    form = RegistrationForm()
    form.build()


def init_registration_routes():
    pass
