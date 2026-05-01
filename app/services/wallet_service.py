import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate
from app.utils.enums import TransactionType, TransactionStatus
from app.config import settings

async def create_deposit_request(db: AsyncSession, user_id: uuid.UUID, txn_in: TransactionCreate) -> Transaction:
    txn = Transaction(
        user_id=user_id,
        type=TransactionType.deposit,
        status=TransactionStatus.pending,
        amount=txn_in.amount,
        currency=txn_in.currency,
        crypto_address_sent_to=txn_in.crypto_address_sent_to,
        txn_hash=txn_in.txn_hash,
        crypto_network=txn_in.crypto_network
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn

async def approve_deposit(db: AsyncSession, txn_id: uuid.UUID, admin_id: uuid.UUID, usd_amount: Decimal) -> Transaction:
    txn_desc = await db.execute(select(Transaction).where(Transaction.id == txn_id))
    txn = txn_desc.scalars().first()
    if not txn or txn.type != TransactionType.deposit or txn.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Invalid transaction or already processed")
        
    wallet_query = await db.execute(select(Wallet).where(Wallet.user_id == txn.user_id))
    wallet = wallet_query.scalars().first()
    
    txn.status = TransactionStatus.approved
    txn.usd_equivalent = usd_amount
    txn.reviewed_by_id = admin_id
    
    wallet.balance += usd_amount
    wallet.total_deposited += txn.amount # raw amount or usd_amount depending on logic?
    
    # Process referral bonus if first deposit
    await process_referral_bonus_if_applicable(db, txn.user_id, usd_amount)
    
    await db.commit()
    await db.refresh(txn)
    return txn

async def process_referral_bonus_if_applicable(db: AsyncSession, user_id: uuid.UUID, usd_amount: Decimal):
    user_q = await db.execute(select(User).where(User.id == user_id))
    user = user_q.scalars().first()
    if not user or not user.referred_by_id:
        return
        
    deposits_q = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id, 
            Transaction.type == TransactionType.deposit,
            Transaction.status == TransactionStatus.approved
        )
    )
    deposits = deposits_q.scalars().all()
    if len(deposits) > 1:
        return # already triggered on previous deposit
        
    bonus = usd_amount * Decimal(settings.REFERRAL_BONUS_PERCENT / 100)
    
    ref_wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == user.referred_by_id))
    ref_wallet = ref_wallet_q.scalars().first()
    
    if ref_wallet:
        ref_wallet.balance += bonus
        ref_wallet.referral_bonus += bonus
