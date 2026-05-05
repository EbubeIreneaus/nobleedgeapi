from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decimal import Decimal
from datetime import datetime, timezone
from app.models.user import User
from app.models.wallet import Wallet
from app.models.settings import Setting
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate
from app.schemas.wallet import WalletConnectRequest
from app.services.wallet_service import create_deposit_request
from app.dependencies import get_db, get_current_active_user
from app.config import settings
from app.utils.enums import TransactionType, TransactionStatus
from app.services.email_service import send_transaction_initiated_email

router = APIRouter()

def _tx_dict(tx: Transaction) -> dict:
    return {
        "id": str(tx.id),
        "type": tx.type.value,
        "amount": float(tx.amount),
        "currency": tx.currency,
        "status": tx.status.value,
        "txn_hash": tx.txn_hash,
        "withdrawal_address": tx.withdrawal_address,
        "withdrawal_network": tx.withdrawal_network,
        "admin_note": tx.admin_note,
        "usd_equivalent": float(tx.usd_equivalent) if tx.usd_equivalent is not None else None,
        "created_at": tx.created_at.isoformat(),
    }

@router.get("/")
async def get_wallet(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = query.scalars().first()
    return {
        "success": True,
        "message": "Wallet retrieved",
        "data": {
            "balance": float(wallet.balance),
            "invested_balance": float(wallet.invested_balance),
            "total_deposited": float(wallet.total_deposited),
            "total_withdrawn": float(wallet.total_withdrawn),
            "total_earned": float(wallet.total_earned),
            "referral_bonus": float(wallet.referral_bonus),
            "connected_wallet": wallet.connected_wallet
        }
    }

@router.get("/deposit/addresses")
async def get_deposit_addresses(db: AsyncSession = Depends(get_db)):
    async def get_val(key: str, default: str) -> str:
        res = await db.execute(select(Setting).where(Setting.key == key))
        s = res.scalars().first()
        return s.value if s else default

    return {
        "success": True,
        "data": {
            "BTC": await get_val("btc_deposit_address", settings.BTC_WALLET),
            "USDT_TRC20": await get_val("usdt_trc20_deposit_address", settings.USDT_TRC20_WALLET),
            "USDT_ERC20": await get_val("usdt_erc20_deposit_address", settings.USDT_ERC20_WALLET),
            "ETH": await get_val("eth_deposit_address", settings.ETH_WALLET),
            "ZELLE": await get_val("zelle_deposit_address", ""),
            "APPLE_PAY": await get_val("apple_pay_deposit_address", ""),
            "PAYPAL": await get_val("paypal_deposit_address", ""),
            "BANK_TRANSFER": await get_val("bank_transfer_deposit_address", "")
        }
    }

@router.post("/connect")
async def connect_wallet(req: WalletConnectRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = query.scalars().first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
        
    wallet.connected_wallet = req.address
    await db.commit()
    
    return {
        "success": True,
        "message": "Wallet connected securely",
        "data": {"connected_wallet": wallet.connected_wallet}
    }

@router.post("/deposit")
async def submit_deposit(txn_in: TransactionCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    txn = await create_deposit_request(db, current_user.id, txn_in)
    
    name = current_user.full_name if hasattr(current_user, "full_name") and current_user.full_name else current_user.username
    background_tasks.add_task(
        send_transaction_initiated_email,
        email=current_user.email,
        name=name,
        tx_type="deposit",
        amount=float(txn_in.amount),
        currency="USD",
        reference=str(txn.id)[:8].upper(),
        status=txn.status.value
    )
    return {
        "success": True,
        "message": "Deposit request submitted",
        "data": {"id": str(txn.id), "status": txn.status.value}
    }

@router.post("/withdraw")
async def submit_withdrawal(
    withdrawal_data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    amount = Decimal(str(withdrawal_data.get("amount", 0)))
    address = withdrawal_data.get("withdrawal_address", "").strip()
    network = withdrawal_data.get("withdrawal_network", "").strip()

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid withdrawal amount")
    if not address:
        raise HTTPException(status_code=400, detail="Withdrawal address is required")
    if not network:
        raise HTTPException(status_code=400, detail="Withdrawal network is required")

    # Check balance
    wallet_q = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = wallet_q.scalars().first()
    if not wallet or wallet.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    # Deduct balance immediately (hold)
    wallet.balance -= amount
    wallet.total_withdrawn += amount

    # Create pending withdrawal transaction
    txn = Transaction(
        user_id=current_user.id,
        type=TransactionType.withdrawal,
        amount=amount,
        currency="USD",
        status=TransactionStatus.pending,
        withdrawal_address=address,
        withdrawal_network=network,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    name = current_user.full_name if hasattr(current_user, "full_name") and current_user.full_name else current_user.username
    background_tasks.add_task(
        send_transaction_initiated_email,
        email=current_user.email,
        name=name,
        tx_type="withdrawal",
        amount=float(amount),
        currency="USD",
        reference=str(txn.id)[:8].upper(),
        status=txn.status.value,
        note=f"To {network} address: {address[:10]}..."
    )

    return {
        "success": True,
        "message": "Withdrawal request submitted. It will be processed within 24 hours.",
        "data": {"id": str(txn.id), "status": txn.status.value}
    }

@router.get("/transactions")
async def list_user_transactions(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    txns = query.scalars().all()

    return {
        "success": True,
        "data": [_tx_dict(tx) for tx in txns]
    }
