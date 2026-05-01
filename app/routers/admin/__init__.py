from fastapi import APIRouter, Depends
from app.dependencies import require_admin
from app.routers.admin.dashboard import router as dashboard_router
from app.routers.admin.users import router as users_router
from app.routers.admin.transactions import router as transactions_router
from app.routers.admin.investments import router as investments_router
from app.routers.admin.plans import router as plans_router

admin_router = APIRouter(dependencies=[Depends(require_admin)])

admin_router.include_router(dashboard_router, prefix="/dashboard", tags=["admin-dashboard"])
admin_router.include_router(users_router, prefix="/users", tags=["admin-users"])
admin_router.include_router(transactions_router, prefix="/transactions", tags=["admin-transactions"])
admin_router.include_router(investments_router, prefix="/investments", tags=["admin-investments"])
admin_router.include_router(plans_router, prefix="/plans", tags=["admin-plans"])
