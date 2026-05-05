from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.wallet import Wallet
from app.dependencies import get_db, get_current_active_user
from app.services.email_service import send_admin_activity_notification
from datetime import datetime, timezone, timedelta

router = APIRouter()

@router.get("/profile")
async def get_profile(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user), 
    db: AsyncSession = Depends(get_db)
):
    wallet_query = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_query.scalars().first()
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if current_user.role not in ["admin", "superadmin"]:
        if not current_user.last_login or (now - current_user.last_login) > timedelta(minutes=30):
            current_user.last_login = now
            await db.commit()
            
            name = current_user.full_name if hasattr(current_user, "full_name") and current_user.full_name else current_user.username
            ip_address = request.client.host if request.client else None
            background_tasks.add_task(
                send_admin_activity_notification,
                email=current_user.email,
                name=name,
                activity_type="visited the site",
                ip_address=ip_address
            )

    return {
        "success": True,
        "message": "Profile retrieved",
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "country": current_user.country,
            "profile_picture": current_user.profile_picture,
            "role": str(current_user.role.value) if hasattr(current_user.role, "value") else str(current_user.role),
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "is_banned": current_user.is_banned,
            "kyc_status": str(current_user.kyc_status.value) if hasattr(current_user.kyc_status, "value") else str(current_user.kyc_status),
            "referral_code": current_user.referral_code,
            "referred_by_id": str(current_user.referred_by_id) if current_user.referred_by_id else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat(),
            "wallet": {
                "id": str(wallet.id),
                "balance": float(wallet.balance),
                "invested_balance": float(wallet.invested_balance),
                "total_deposited": float(wallet.total_deposited),
                "total_withdrawn": float(wallet.total_withdrawn),
                "total_earned": float(wallet.total_earned),
                "referral_bonus": float(wallet.referral_bonus),
            } if wallet else None
        }
    }
