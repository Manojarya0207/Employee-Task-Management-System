from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from config import (
    STORAGE_SECRET,
    DEFAULT_ADMIN_ID,
    DEFAULT_ADMIN_PASSWORD,
    HOST,
    PORT,
    IS_PRODUCTION,
)
from models import Base, engine, SessionLocal
from models.employee import Employee
from models.task import Task
from models.activity_log import ActivityLog
from services.auth_service import hash_password

from pages.login import init_login_routes
from pages.register import init_registration_routes
from pages.admin import init_admin_routes
from pages.employee import init_employee_routes
from pages.reports import init_reports_routes

from utils.logging_config import configure_logging
from utils.error_pages import register_error_pages
from utils.db_migration import run_migrations

from datetime import date

# Configure application-wide logging (console + rotating file).
logger = configure_logging()

# 1. Initialize Database Tables
def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")

    # Seed default administrator account if database is empty
    db = SessionLocal()
    try:
        admin_user = db.query(Employee).filter(Employee.employee_id == DEFAULT_ADMIN_ID).first()
        if not admin_user:
            logger.info("Seeding database with default administrator account...")
            default_admin = Employee(
                employee_id=DEFAULT_ADMIN_ID,
                employee_name="System Administrator",
                phone_number="9999999999",
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="admin",
                department="Management",
                status="active",
                joining_date=date.today(),
                registration_status="approved",   # Admin is always approved
            )
            db.add(default_admin)
            db.commit()
            logger.info("Database seeded successfully.")
    except Exception as e:
        logger.error("Error seeding database: %s", e)
        db.rollback()
    finally:
        db.close()

# 2. Access Control and Role Authorization Middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Unrestricted path matches (NiceGUI internal paths, static files, login, and register)
        unrestricted_prefixes = ('/login', '/register', '/_nicegui', '/static', '/favicon.ico')
        if any(path.startswith(prefix) for prefix in unrestricted_prefixes):
            return await call_next(request)

        # Authentication check
        session = app.storage.user
        if not session or not session.get('authenticated', False):
            # Remember path and redirect to login
            session['referrer_path'] = path
            return RedirectResponse('/login')

        # Role-based Authorization check
        role = session.get('role', 'employee')

        # Block employees from accessing admin portals
        if path.startswith('/admin') and role != 'admin':
            return RedirectResponse('/employee')

        # Block admins from accessing employee portals
        if path.startswith('/employee') and role != 'employee':
            return RedirectResponse('/admin')

        return await call_next(request)

# 3. Mount routes and configure app
init_db()
run_migrations()   # Safe, idempotent — adds new columns and backfills existing rows

# Add auth check middleware
app.add_middleware(AuthMiddleware)

# Register branded 403 / 404 / 500 error pages
register_error_pages(app)

# Add static file paths
app.add_static_files('/static', 'static')

# Page Routes registration
init_login_routes()
init_registration_routes()
init_admin_routes()
init_employee_routes()
init_reports_routes()

# Root landing route redirection
@ui.page('/')
def root_page():
    if app.storage.user.get('authenticated', False):
        role = app.storage.user.get('role')
        ui.navigate.to('/admin' if role == 'admin' else '/employee')
    else:
        ui.navigate.to('/login')

# Logout route
@ui.page('/logout')
def logout_page():
    app.storage.user.clear()
    ui.navigate.to('/login')

if __name__ in {"__main__", "__mp_main__"}:
    # Host/port/secret all come from the environment (see config.py) so the same
    # command works locally and on Render, which supplies the PORT to bind to.
    logger.info("Starting TaskFlow on %s:%s (production=%s)", HOST, PORT, IS_PRODUCTION)
    ui.run(
        title='TaskFlow - Task Management System',
        storage_secret=STORAGE_SECRET,
        host=HOST,
        port=PORT,
        reload=not IS_PRODUCTION,  # auto-reload during development only
        show=False,  # never open a browser in server environments
    )

