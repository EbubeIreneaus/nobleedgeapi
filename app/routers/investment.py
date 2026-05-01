from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.plan import InvestmentPlan
from app.models.investment import Investment
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.investment import InvestmentCreate
from app.dependencies import get_db, get_current_active_user
from app.utils.enums import InvestmentStatus, TransactionType, TransactionStatus

router = APIRouter()

@router.get("/plans")
async def get_plans(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(InvestmentPlan).where(InvestmentPlan.is_active == True))
    plans = query.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "min_amount": float(p.min_amount),
                "max_amount": float(p.max_amount) if p.max_amount else None,
                "roi_percent": float(p.roi_percent),
                "roi_cycle": p.roi_cycle.value,
                "duration_days": p.duration_days,
                "capital_returned": p.capital_returned,
                "color": p.color,
                "features": p.features
            } for p in plans
        ]
    }

@router.post("/")
async def create_investment(inv_in: InvestmentCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    # Verify plan
    plan_query = await db.execute(select(InvestmentPlan).where(InvestmentPlan.id == inv_in.plan_id))
    plan = plan_query.scalars().first()
    
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")
        
    if inv_in.amount < plan.min_amount or (plan.max_amount and inv_in.amount > plan.max_amount):
        raise HTTPException(status_code=400, detail="Amount out of bounds for plan")
        
    # Verify wallet balance
    wallet_query = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_query.scalars().first()
    
    if wallet.balance < inv_in.amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        
    # Deduct and lock
    wallet.balance -= inv_in.amount
    wallet.invested_balance += inv_in.amount
    
    # Calculate cycle total
    cycles_total = 0
    if plan.roi_cycle.value == "daily":
        cycles_total = plan.duration_days
    elif plan.roi_cycle.value == "weekly":
        cycles_total = plan.duration_days // 7
    elif plan.roi_cycle.value == "monthly":
        cycles_total = plan.duration_days // 30
        
    total_return_expected = inv_in.amount * (plan.total_return_percent / 100)
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    next_roi_date = now + timedelta(days=1)
    if plan.roi_cycle.value == "weekly":
        next_roi_date = now + timedelta(weeks=1)
    elif plan.roi_cycle.value == "monthly":
        next_roi_date = now + timedelta(days=30)
        
    ends_at = now + timedelta(days=plan.duration_days)

    investment = Investment(
        user_id=current_user.id,
        plan_id=plan.id,
        amount=inv_in.amount,
        currency_used=inv_in.currency_used,
        status=InvestmentStatus.active,
        roi_percent=plan.roi_percent,
        roi_cycle=plan.roi_cycle.value,
        duration_days=plan.duration_days,
        total_return_expected=total_return_expected,
        cycles_total=cycles_total,
        next_roi_date=next_roi_date,
        started_at=now,
        ends_at=ends_at
    )
    
    db.add(investment)
    await db.flush()
    
    # Create config transaction
    txn = Transaction(
        user_id=current_user.id,
        type=TransactionType.investment,
        status=TransactionStatus.completed,
        amount=inv_in.amount,
        currency="USD",
        usd_equivalent=inv_in.amount,
        investment_id=investment.id
    )
    db.add(txn)
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Investment created successfully"
    }

@router.get("/")
async def list_investments(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Investment).where(Investment.user_id == current_user.id))
    investments = query.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(i.id),
                "amount": float(i.amount),
                "status": i.status.value,
                "cycles_completed": i.cycles_completed,
                "cycles_total": i.cycles_total,
                "total_return_paid": float(i.total_return_paid)
            } for i in investments
        ]
    }
