from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.user import User
from app.models.wallet import Wallet
from app.models.investment import Investment
from app.models.transaction import Transaction
from app.dependencies import get_db

router = APIRouter()

@router.get("/")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Simple aggregations
    user_count = await db.scalar(select(func.count(User.id)))
    active_inv = await db.scalar(select(func.count(Investment.id)).where(Investment.status == 'active'))
    
    total_deposits = await db.scalar(select(func.sum(Transaction.usd_equivalent)).where(Transaction.type == 'deposit', Transaction.status == 'completed'))
    total_withdrawals = await db.scalar(select(func.sum(Transaction.amount)).where(Transaction.type == 'withdrawal', Transaction.status == 'completed'))
    
    return {
        "success": True,
        "data": {
            "total_users": user_count or 0,
            "active_investments": active_inv or 0,
            "total_deposits": float(total_deposits or 0),
            "total_withdrawals": float(total_withdrawals or 0)
        }
    }
