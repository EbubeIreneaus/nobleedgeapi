import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.database import AsyncSessionLocal
from app.models.investment import Investment
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.plan import InvestmentPlan
from app.utils.enums import InvestmentStatus, TransactionType, TransactionStatus
from .email_service import send_investment_roi_email

scheduler = AsyncIOScheduler()

async def process_roi_credits():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        query = await db.execute(
            select(Investment, Wallet, InvestmentPlan)
            .join(Wallet, Investment.user_id == Wallet.user_id)
            .join(InvestmentPlan, Investment.plan_id == InvestmentPlan.id)
            .where(Investment.status == InvestmentStatus.active)
            .where(Investment.next_roi_date <= now)
        )
        
        results = query.all()
        for idx in range(len(results)):
            investment, wallet, plan = results[idx]
            
            roi_amount = investment.amount * (investment.roi_percent / 100)
            
            # Update Wallet
            wallet.balance += roi_amount
            wallet.total_earned += roi_amount
            
            # Create ROI transaction record
            roi_txn = Transaction(
                user_id=investment.user_id,
                type=TransactionType.roi_credit,
                status=TransactionStatus.completed,
                amount=roi_amount,
                currency="USD",
                usd_equivalent=roi_amount,
                investment_id=investment.id
            )
            db.add(roi_txn)
            
            # Update Investment
            investment.cycles_completed += 1
            investment.total_return_paid += roi_amount
            
            if investment.roi_cycle == "daily":
                investment.next_roi_date += timedelta(days=1)
            elif investment.roi_cycle == "weekly":
                investment.next_roi_date += timedelta(weeks=1)
            elif investment.roi_cycle == "monthly":
                investment.next_roi_date += timedelta(days=30)
                
            # Check completion
            if investment.cycles_completed >= investment.cycles_total:
                investment.status = InvestmentStatus.completed
                investment.completed_at = now
                
                # Return Capital
                if plan.capital_returned:
                    wallet.balance += investment.amount
                    wallet.invested_balance -= investment.amount
                    
                    return_capital_txn = Transaction(
                        user_id=investment.user_id,
                        type=TransactionType.refund,
                        status=TransactionStatus.completed,
                        amount=investment.amount,
                        currency="USD",
                        usd_equivalent=investment.amount,
                        investment_id=investment.id,
                        admin_note="Capital returned on completion"
                    )
                    db.add(return_capital_txn)
            
            # TODO: Send ROI credited email
            user_query = await db.execute(select(User).where(User.id == investment.user_id))
            user = user_query.scalars().first()
            if user:
                # Add background task typically, doing it inline for simplicity but we should really use tasks
                pass
                
        await db.commit()

# Start scheduler
def start_scheduler():
    scheduler.add_job(process_roi_credits, "interval", hours=1)
    scheduler.start()
