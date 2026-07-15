from fastapi import APIRouter
from routes.auth_routes import router as auth_router
from routes.employee_routes import router as employee_router
from routes.task_routes import router as task_router
from routes.dashboard_routes import router as dashboard_router
from routes.report_routes import router as report_router
from routes.status_routes import router as status_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(employee_router)
router.include_router(task_router)
router.include_router(dashboard_router)
router.include_router(report_router)
router.include_router(status_router)
