import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration
DB_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URI = f"sqlite:///{os.path.join(DB_DIR, 'taskflow.db')}"

# NiceGUI / Starlette storage session secret
# In production, this should be read from environment variables
STORAGE_SECRET = os.environ.get('STORAGE_SECRET', 'taskflow-super-secret-secure-key-1234567890')

# Default Admin Credentials
DEFAULT_ADMIN_ID = 'admin'
DEFAULT_ADMIN_PASSWORD = 'Admin@123'

# System configs
REMINDER_HOUR = 18  # 6:00 PM
REMINDER_MINUTE = 0

# Status values
STATUS_PENDING = 'Pending'
STATUS_WIP = 'Work In Progress'
STATUS_COMPLETED = 'Completed'
STATUS_BLOCKED = 'Blocked'
STATUS_ON_HOLD = 'On Hold'

STATUS_CHOICES = [
    STATUS_PENDING,
    STATUS_WIP,
    STATUS_COMPLETED,
    STATUS_BLOCKED,
    STATUS_ON_HOLD
]
