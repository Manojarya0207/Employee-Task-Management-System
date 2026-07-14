# TaskFlow — Employee Task Management System

TaskFlow is a role-based web application for assigning, tracking, and reporting on
employee tasks. Administrators manage employees and tasks and export reports;
employees update the status of their own work. It ships production-ready for
one-click deployment to [Render](https://render.com).

> **Tech note:** The UI is built with **NiceGUI** (a Python UI framework running
> on FastAPI/Starlette/Uvicorn), **not** Flask. All pages are defined in Python —
> there are no Jinja templates. The app is a single ASGI service started with
> `python main.py`.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Features](#features)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Run Locally](#run-locally)
- [Environment Variables](#environment-variables)
- [Default Login Credentials](#default-login-credentials)
- [Push to GitHub](#push-to-github)
- [Deploy to Render](#deploy-to-render)
- [Future Improvements](#future-improvements)

---

## Project Overview

TaskFlow provides two portals behind a single login:

- **Admin portal** — create and manage employees, assign and monitor tasks,
  review activity logs, and export reports (Excel/PDF).
- **Employee portal** — view assigned tasks and update their status.

Authentication is session-based with hashed passwords and role-based access
control enforced by middleware. The database layer uses SQLAlchemy, so the app
runs on **SQLite locally** and **PostgreSQL in production** with no code changes.

---

## Technology Stack

| Layer            | Technology                                             |
|------------------|--------------------------------------------------------|
| Language         | Python 3.12                                            |
| UI / Web         | NiceGUI (on FastAPI · Starlette · Uvicorn — ASGI)      |
| ORM              | SQLAlchemy 2.x                                          |
| Database         | SQLite (local) / PostgreSQL (production via `DATABASE_URL`) |
| Auth / Passwords | Werkzeug scrypt hashing + NiceGUI signed sessions      |
| Reporting        | openpyxl (Excel), reportlab (PDF)                       |
| Config           | python-dotenv                                          |
| Hosting          | Render                                                  |
| Version Control  | Git + GitHub                                            |

---

## Features

- 🔐 **Role-based authentication** — separate admin and employee experiences,
  enforced by ASGI middleware (`AuthMiddleware` in `main.py`).
- 👥 **Employee management** — create, edit, deactivate, and delete employees.
- ✅ **Task management** — assign tasks and track status: *Pending, Work In
  Progress, Completed, Blocked, On Hold*.
- 📊 **Reports & exports** — generate Excel and PDF reports.
- 📝 **Activity logging** — audit trail of key user actions.
- 🔑 **Secure passwords** — scrypt hashing; passwords are never stored in plaintext.
- 🌱 **Self-seeding database** — tables and a default admin are created
  automatically on first run.
- 🧯 **Branded error pages** — friendly 403 / 404 / 500 pages.
- 🗒️ **Rotating file + console logging**.

---

## Folder Structure

```
Employee-Task-Management-System/
│
├── main.py                 # App entry point: DB init, middleware, routes, server
├── config.py               # Environment-driven configuration (dev/prod)
├── requirements.txt        # Python dependencies
├── Procfile                # Process definition (web: python main.py)
├── render.yaml             # Render Blueprint for automatic deployment
├── .python-version         # Pins Python 3.12 on Render
├── .env.example            # Sample environment variables
├── .gitignore
│
├── models/                 # SQLAlchemy models + engine/session factory
│   ├── __init__.py         # Engine (SQLite/Postgres aware) + SessionLocal
│   ├── employee.py
│   ├── task.py
│   └── activity_log.py
│
├── pages/                  # NiceGUI page definitions (the UI)
│   ├── login.py
│   ├── admin.py
│   ├── employee.py
│   ├── reports.py
│   └── layout.py
│
├── services/               # Business logic (reusable, framework-agnostic)
│   ├── auth_service.py     # Hashing, authentication, activity logging
│   ├── employee_service.py
│   ├── task_service.py
│   └── report_service.py
│
├── utils/                  # Cross-cutting helpers
│   ├── logging_config.py   # Console + rotating file logging
│   └── error_pages.py      # 403 / 404 / 500 handlers
│
├── static/                 # CSS and static assets
│   └── css/custom.css
│
└── database/               # Local SQLite database (git-ignored)
```

---

## Installation

### 1. Prerequisites
- Python **3.12+**
- Git

### 2. Clone the repository
```bash
git clone https://github.com/<username>/taskflow.git
cd taskflow
```

### 3. Create and activate a virtual environment
A virtual environment isolates this project's dependencies from your system Python.

```bash
# Create it
python -m venv venv

# Activate it
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows (PowerShell/CMD)
```
Your shell prompt will show `(venv)` when it's active. Deactivate any time with `deactivate`.

### 4. Install requirements
```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file
```bash
cp .env.example .env          # then edit values as needed
```

---

## Run Locally

```bash
python main.py
```

Then open **http://localhost:8080**.

On first run the app automatically:
1. Creates the `database/` folder and SQLite file,
2. Creates all tables, and
3. Seeds the default admin account (see below).

---

## Environment Variables

| Variable                  | Required | Default                 | Description                                                        |
|---------------------------|----------|-------------------------|--------------------------------------------------------------------|
| `STORAGE_SECRET`          | Prod     | dev fallback            | Signs session cookies. Use a long random string. (`SECRET_KEY` alias accepted.) |
| `DATABASE_URL`            | No       | local SQLite            | PostgreSQL connection string; when unset, SQLite is used.          |
| `ENVIRONMENT`             | No       | auto-detected           | `development` or `production`. Render is auto-detected.            |
| `PORT`                    | No       | `8080`                  | Port to bind. Render sets this automatically.                     |
| `LOG_LEVEL`               | No       | `INFO` (prod) / `DEBUG` | Logging verbosity.                                                 |
| `DEFAULT_ADMIN_ID`        | No       | `admin`                 | Seeded admin ID (empty DB only).                                  |
| `DEFAULT_ADMIN_PASSWORD`  | No       | `Admin@123`             | Seeded admin password (empty DB only).                            |

Generate a secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Default Login Credentials

Created automatically when the database is empty. **Change the admin password
immediately after first login.**

**Admin**
- Employee ID: `admin`
- Password: `Admin@123`

**Employees**
- Employees do not self-register. Sign in as admin and create employees from the
  admin portal; each is given an Employee ID and password to log in with.

---

## Push to GitHub

Every command below, explained:

```bash
git init
```
Initializes a new local Git repository in the current folder.

```bash
git add .
```
Stages **all** files (respecting `.gitignore`) for the next commit.

```bash
git commit -m "Initial Commit"
```
Records the staged files as a snapshot with the given message.

```bash
git branch -M main
```
Renames the current branch to `main` (the modern default), `-M` forces the rename.

```bash
git remote add origin https://github.com/<username>/taskflow.git
```
Links your local repo to the remote GitHub repository, naming it `origin`.
Create the empty repo on GitHub first, then replace `<username>`.

```bash
git push -u origin main
```
Uploads `main` to GitHub and sets it as the upstream (`-u`), so future pushes are
just `git push`.

---

## Deploy to Render

This repo includes a `render.yaml` Blueprint, so deployment is automatic.

### Option A — Blueprint (recommended)
1. Push the project to GitHub (above).
2. In the [Render dashboard](https://dashboard.render.com) click **New → Blueprint**.
3. **Connect your GitHub account** and select the `taskflow` repository.
4. Render reads `render.yaml`, provisions the web service, and generates a
   `STORAGE_SECRET` for you. Click **Apply**.

### Option B — Manual Web Service
1. **New → Web Service**, connect GitHub, pick the repo.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `python main.py`
4. Add environment variables (`STORAGE_SECRET`, `ENVIRONMENT=production`, and
   optionally `DATABASE_URL`).
5. Click **Create Web Service**.

### How automatic deployment works
With `autoDeploy: true` (default), **every push to your connected branch triggers
a new build and deploy** — no manual step required. Render installs dependencies,
runs the start command, binds to its injected `PORT`, and routes traffic to the app.

### How to redeploy
- **Automatically:** `git push` — Render rebuilds on each push.
- **Manually:** Render dashboard → your service → **Manual Deploy → Deploy latest commit**
  (or **Clear build cache & deploy**).

> ⚠️ **Data persistence:** Render's free filesystem is **ephemeral** — the SQLite
> file is wiped on every deploy/restart. For persistent data, uncomment the
> PostgreSQL database + `DATABASE_URL` in `render.yaml` (or add a database and set
> `DATABASE_URL`). No code changes are needed — `config.py` picks it up automatically.

---

## Future Improvements

- Email/SMS task reminders (schedule scaffolding exists in `config.py`).
- Password-reset and self-service account recovery flows.
- Pagination, search, and advanced filtering on task/employee lists.
- Configurable roles and granular permissions beyond admin/employee.
- Automated test suite (pytest) and CI on GitHub Actions.
- Dockerfile for container-based deployments.

---

_Built with NiceGUI, SQLAlchemy, and Render._
