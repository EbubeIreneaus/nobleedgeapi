from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.wallet import Wallet
from app.dependencies import get_db, get_current_active_user
from uuid import UUID

router = APIRouter()

def _user_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "role": u.role.value if hasattr(u.role, "value") else u.role,
        "is_banned": u.is_banned,
        "is_active": u.is_active if hasattr(u, "is_active") else True,
        "kyc_status": u.kyc_status.value if hasattr(u, "kyc_status") and u.kyc_status else "none",
        "referral_code": u.referral_code if hasattr(u, "referral_code") else None,
        "created_at": u.created_at.isoformat() if hasattr(u, "created_at") and u.created_at else None,
    }

@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    query = await db.execute(select(User).order_by(User.created_at.desc() if hasattr(User, "created_at") else User.email))
    users = query.scalars().all()
    return {"success": True, "data": [_user_dict(u) for u in users]}

@router.get("/{id}/wallet")
async def get_user_wallet(id: UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {
        "success": True,
        "data": {
            "balance": float(wallet.balance),
            "invested_balance": float(wallet.invested_balance),
            "total_deposited": float(wallet.total_deposited),
            "total_withdrawn": float(wallet.total_withdrawn),
            "total_earned": float(wallet.total_earned),
        }
    }

@router.patch("/{id}/ban")
async def ban_user(id: UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    query = await db.execute(select(User).where(User.id == id))
    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (user.role.value if hasattr(user.role, "value") else user.role) == "superadmin":
        raise HTTPException(status_code=400, detail="Cannot ban superadmin")
    user.is_banned = True
    await db.commit()
    return {"success": True, "message": "User banned"}

@router.patch("/{id}/unban")
async def unban_user(id: UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    query = await db.execute(select(User).where(User.id == id))
    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False
    await db.commit()
    return {"success": True, "message": "User unbanned"}
