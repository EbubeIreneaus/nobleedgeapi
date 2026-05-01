from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.investment import Investment
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.utils.enums import InvestmentStatus, TransactionType, TransactionStatus
from app.dependencies import get_db, require_superadmin

router = APIRouter()

@router.get("/")
async def list_all_investments(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Investment))
    investments = query.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(i.id),
                "user_id": str(i.user_id),
                "amount": float(i.amount),
                "status": i.status.value,
                "started_at": i.started_at
            } for i in investments
        ]
    }

@router.patch("/{id}/cancel")
async def cancel_investment(id: str, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Investment).where(Investment.id == id))
    inv = query.scalars().first()
    if not inv or inv.status != InvestmentStatus.active:
        raise HTTPException(status_code=400, detail="Cannot cancel this investment")
        
    inv.status = InvestmentStatus.cancelled
    
    # Refund capital
    wallet_query = await db.execute(select(Wallet).where(Wallet.user_id == inv.user_id))
    wallet = wallet_query.scalars().first()
    
    wallet.invested_balance -= inv.amount
    wallet.balance += inv.amount
    
    refund_txn = Transaction(
        user_id=inv.user_id,
        type=TransactionType.refund,
        status=TransactionStatus.completed,
        amount=inv.amount,
        currency="USD",
        usd_equivalent=inv.amount,
        investment_id=inv.id,
        admin_note="Investment cancelled manually by admin"
    )
    db.add(refund_txn)
    
    await db.commit()
    return {"success": True, "message": "Investment cancelled and capital refunded"}
    
@router.post("/roi/run")
async def force_roi_run(current_user = Depends(require_superadmin)):
    from app.services.roi_scheduler import process_roi_credits
    await process_roi_credits()
    return {"success": True, "message": "ROI calculations triggered manually"}
