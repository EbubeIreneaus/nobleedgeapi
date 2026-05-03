from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.wallet import Wallet
from app.dependencies import get_db, get_current_active_user
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from app.services.email_service import send_plain_email

class AmountPayload(BaseModel):
    amount: float

class ProfitPayload(BaseModel):
    total_earned: float

class EmailPayload(BaseModel):
    subject: str
    body: str

router = APIRouter()

def _user_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "phone": u.phone,
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

@router.post("/{id}/add-deposit")
async def add_deposit_to_user(id: UUID, payload: AmountPayload, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    amount = Decimal(str(payload.amount))
    wallet.balance += amount
    wallet.total_deposited += amount
    await db.commit()
    return {"success": True, "message": "Deposit added"}

@router.post("/{id}/deduct-funds")
async def deduct_funds_from_user(id: UUID, payload: AmountPayload, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    amount = Decimal(str(payload.amount))
    wallet.balance -= amount
    wallet.total_deposited -= amount
    await db.commit()
    return {"success": True, "message": "Funds deducted"}

@router.post("/{id}/deduct-profit")
async def deduct_profit_from_user(id: UUID, payload: AmountPayload, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    amount = Decimal(str(payload.amount))
    wallet.balance -= amount
    wallet.total_earned -= amount
    await db.commit()
    return {"success": True, "message": "Profit deducted"}

@router.patch("/{id}/edit-profit")
async def edit_user_profit(id: UUID, payload: ProfitPayload, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    new_earned = Decimal(str(payload.total_earned))
    diff = new_earned - wallet.total_earned
    wallet.balance += diff
    wallet.total_earned = new_earned
    await db.commit()
    return {"success": True, "message": "Profit edited"}

@router.post("/{id}/send-email")
async def send_email_to_user(id: UUID, payload: EmailPayload, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    user_q = await db.execute(select(User).where(User.id == id))
    user = user_q.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await send_plain_email(
        email_to=user.email,
        subject=payload.subject,
        body=payload.body
    )
    return {"success": True, "message": "Email sent"}
