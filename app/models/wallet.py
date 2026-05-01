from datetime import datetime, timezone
import uuid
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Numeric, String

from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    invested_balance: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    total_deposited: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    total_withdrawn: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    total_earned: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    referral_bonus: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal('0'))
    
    btc_deposit_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    eth_deposit_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    usdt_trc20_deposit_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    usdt_erc20_deposit_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet")
