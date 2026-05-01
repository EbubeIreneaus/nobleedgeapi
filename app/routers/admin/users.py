from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.models.user import User
from app.models.wallet import Wallet
from app.dependencies import get_db, get_current_active_user
from app.services.email_service import send_plain_email
from uuid import UUID
from decimal import Decimal

router = APIRouter()

# ── Request Models ──────────────────────────────────────
class AddDepositRequest(BaseModel):
    amount: float

class DeductFundsRequest(BaseModel):
    amount: float

class EditProfitRequest(BaseModel):
    total_earned: float

class SendEmailRequest(BaseModel):
    subject: str
    body: str

class DeductProfitRequest(BaseModel):
    amount: float

class EditDepositAddressesRequest(BaseModel):
    btc_deposit_address: str | None = None
    eth_deposit_address: str | None = None
    usdt_trc20_deposit_address: str | None = None
    usdt_erc20_deposit_address: str | None = None

def _user_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "role": u.role.value if hasattr(u.role, "value") else u.role,
        "is_banned": u.is_banned,
        "is_active": u.is_active if hasattr(u, "is_active") else True,
        "kyc_status": u.kyc_status.value if hasattr(u, "kyc_status") and u.kyc_status else "none",
        "referral_code": u.referral_code if hasattr(u, "referral_code") else None,
        "phone": u.phone if hasattr(u, "phone") else None,
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
async def add_deposit_to_user(
    id: UUID, 
    req: AddDepositRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Add deposit funds to user's account"""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet.balance += Decimal(str(req.amount))
    wallet.total_deposited += Decimal(str(req.amount))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Deposited ${req.amount} to user's account",
        "new_balance": float(wallet.balance)
    }

@router.post("/{id}/deduct-funds")
async def deduct_funds_from_user(
    id: UUID, 
    req: DeductFundsRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Deduct funds from user's account"""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    if wallet.balance < Decimal(str(req.amount)):
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    wallet.balance -= Decimal(str(req.amount))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Deducted ${req.amount} from user's account",
        "new_balance": float(wallet.balance)
    }

@router.patch("/{id}/edit-profit")
async def edit_total_profit(
    id: UUID, 
    req: EditProfitRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Edit user's total earned/profit"""
    if req.total_earned < 0:
        raise HTTPException(status_code=400, detail="Total earned cannot be negative")
    
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet.total_earned = Decimal(str(req.total_earned))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Updated user's total profit to ${req.total_earned}",
        "total_earned": float(wallet.total_earned)
    }

@router.post("/{id}/deduct-profit")
async def deduct_user_profit(
    id: UUID, 
    req: DeductProfitRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Deduct from user's total profit"""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet.total_earned -= Decimal(str(req.amount))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Deducted ${req.amount} from user's total profit",
        "total_earned": float(wallet.total_earned)
    }

@router.patch("/{id}/deposit-addresses")
async def edit_deposit_addresses(
    id: UUID, 
    req: EditDepositAddressesRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Edit user's specific deposit addresses"""
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == id))
    wallet = wallet_q.scalars().first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet.btc_deposit_address = req.btc_deposit_address
    wallet.eth_deposit_address = req.eth_deposit_address
    wallet.usdt_trc20_deposit_address = req.usdt_trc20_deposit_address
    wallet.usdt_erc20_deposit_address = req.usdt_erc20_deposit_address
    await db.commit()
    
    return {
        "success": True,
        "message": "User's deposit addresses updated successfully"
    }

@router.post("/{id}/send-email")
async def send_email_to_user(
    id: UUID, 
    req: SendEmailRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_active_user)
):
    """Admin: Send email to user"""
    query = await db.execute(select(User).where(User.id == id))
    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not req.subject or not req.body:
        raise HTTPException(status_code=400, detail="Subject and body are required")
    
    try:
        await send_plain_email(
            email_to=user.email,
            subject=req.subject,
            body=req.body
        )
        return {"success": True, "message": f"Email sent to {user.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
