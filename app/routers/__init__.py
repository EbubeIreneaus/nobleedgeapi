from fastapi import APIRouter
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.wallet import router as wallet_router
from app.routers.investment import router as investment_router
from app.routers.referral import router as referral_router
from app.routers.admin import admin_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/user", tags=["user"])
api_router.include_router(wallet_router, prefix="/wallet", tags=["wallet"])
api_router.include_router(investment_router, prefix="/investments", tags=["investments"])
api_router.include_router(referral_router, prefix="/referrals", tags=["referrals"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
