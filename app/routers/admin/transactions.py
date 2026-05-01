from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decimal import Decimal
from datetime import datetime, timezone
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.models.user import User
from app.dependencies import get_db, get_current_active_user
from app.utils.enums import TransactionStatus, TransactionType
from app.services.wallet_service import approve_deposit
from app.services.email_service import send_transaction_approved_email
from uuid import UUID

router = APIRouter()

def _tx_dict(t: Transaction, user: User | None = None) -> dict:
    d = {
        "id": str(t.id),
        "user_id": str(t.user_id),
        "type": t.type.value,
        "amount": float(t.amount),
        "currency": t.currency,
        "status": t.status.value,
        "txn_hash": t.txn_hash,
        "withdrawal_address": t.withdrawal_address,
        "withdrawal_network": t.withdrawal_network,
        "admin_note": t.admin_note,
        "usd_equivalent": float(t.usd_equivalent) if t.usd_equivalent is not None else None,
        "created_at": t.created_at.isoformat(),
    }
    if user:
        d["user_email"] = user.email
        d["user_name"] = f"{user.first_name} {user.last_name}".strip() if hasattr(user, "first_name") else user.email
    return d

@router.get("/")
async def list_all_transactions(
    type: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    q = select(Transaction).order_by(Transaction.created_at.desc())
    if type:
        q = q.where(Transaction.type == type)
    if status:
        q = q.where(Transaction.status == status)
    result = await db.execute(q)
    transactions = result.scalars().all()

    # Batch-load users for email display
    user_ids = list({t.user_id for t in transactions})
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    return {
        "success": True,
        "data": [_tx_dict(t, users_map.get(t.user_id)) for t in transactions]
    }

@router.get("/deposits")
async def list_deposits(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Transaction).where(Transaction.type == TransactionType.deposit).order_by(Transaction.created_at.desc()))
    transactions = query.scalars().all()
    return {
        "success": True,
        "data": [_tx_dict(t) for t in transactions]
    }

@router.get("/withdrawals")
async def list_withdrawals(db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Transaction).where(Transaction.type == TransactionType.withdrawal).order_by(Transaction.created_at.desc()))
    transactions = query.scalars().all()
    return {
        "success": True,
        "data": [_tx_dict(t) for t in transactions]
    }

@router.patch("/deposits/{id}/approve")
async def approve_deposit_endpoint(id: UUID, background_tasks: BackgroundTasks, usd_amount: Decimal = Query(...), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    txn = await approve_deposit(db, id, current_user.id, usd_amount)
    
    user_q = await db.execute(select(User).where(User.id == txn.user_id))
    target_user = user_q.scalars().first()
    if target_user:
        name = target_user.full_name if hasattr(target_user, "full_name") and target_user.full_name else target_user.username
        background_tasks.add_task(
            send_transaction_approved_email,
            email=target_user.email,
            name=name,
            tx_type="deposit",
            amount=float(txn.amount),
            currency=txn.currency,
            reference=str(txn.id)[:8].upper()
        )

    return {
        "success": True,
        "message": "Deposit approved",
        "data": {"status": txn.status.value, "usd_equivalent": float(txn.usd_equivalent)}
    }

@router.patch("/deposits/{id}/reject")
async def reject_deposit(id: UUID, admin_note: str = Query(None), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Transaction).where(Transaction.id == id, Transaction.type == TransactionType.deposit))
    txn = query.scalars().first()
    if not txn or txn.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Invalid or non-pending transaction")
    txn.status = TransactionStatus.rejected
    txn.admin_note = admin_note
    txn.reviewed_by_id = current_user.id
    txn.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    return {"success": True, "message": "Deposit rejected"}

@router.patch("/withdrawals/{id}/approve")
async def approve_withdrawal(id: UUID, background_tasks: BackgroundTasks, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Transaction).where(Transaction.id == id, Transaction.type == TransactionType.withdrawal))
    txn = query.scalars().first()
    if not txn or txn.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Invalid or non-pending withdrawal")
    txn.status = TransactionStatus.completed
    txn.reviewed_by_id = current_user.id
    txn.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Deduct from available balance and increase total_withdrawn
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == txn.user_id))
    wallet = wallet_q.scalars().first()
    if wallet:
        wallet.balance -= txn.amount
        wallet.total_withdrawn += txn.amount

    await db.commit()

    user_q = await db.execute(select(User).where(User.id == txn.user_id))
    target_user = user_q.scalars().first()
    if target_user:
        name = target_user.full_name if hasattr(target_user, "full_name") and target_user.full_name else target_user.username
        background_tasks.add_task(
            send_transaction_approved_email,
            email=target_user.email,
            name=name,
            tx_type="withdrawal",
            amount=float(txn.amount),
            currency=txn.currency,
            reference=str(txn.id)[:8].upper()
        )

    return {"success": True, "message": "Withdrawal approved and processed"}

@router.patch("/withdrawals/{id}/reject")
async def reject_withdrawal(id: UUID, admin_note: str = Query(None), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Transaction).where(Transaction.id == id, Transaction.type == TransactionType.withdrawal))
    txn = query.scalars().first()
    if not txn or txn.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Invalid or non-pending withdrawal")

    # We no longer refund balance here because it is not deducted until approval.

    txn.status = TransactionStatus.rejected
    txn.admin_note = admin_note
    txn.reviewed_by_id = current_user.id
    txn.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    return {"success": True, "message": "Withdrawal rejected and balance refunded"}
