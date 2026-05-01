from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.referral import Referral
from app.dependencies import get_db, get_current_active_user

router = APIRouter()

@router.get("/")
async def get_referral_stats(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Referral).where(Referral.referrer_id == current_user.id))
    referrals = query.scalars().all()
    
    total_earned = sum(float(r.bonus_amount) for r in referrals if r.status.value == "credited")
    total_pending = sum(float(r.bonus_amount) for r in referrals if r.status.value == "pending")
    
    return {
        "success": True,
        "data": {
            "total_referred": len(referrals),
            "total_earned": total_earned,
            "total_pending": total_pending
        }
    }

@router.get("/link")
async def get_referral_link(current_user: User = Depends(get_current_active_user)):
    return {
        "success": True,
        "data": {
            "referral_code": current_user.referral_code,
            # Ideally use FRONTEND_URL from settings
            "referral_link": f"http://localhost:3000/register?ref={current_user.referral_code}"
        }
    }

@router.get("/history")
async def get_referral_history(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Referral).where(Referral.referrer_id == current_user.id))
    referrals = query.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id),
                "referee_id": str(r.referee_id),
                "bonus_amount": float(r.bonus_amount),
                "status": r.status.value,
                "created_at": r.created_at
            } for r in referrals
        ]
    }
