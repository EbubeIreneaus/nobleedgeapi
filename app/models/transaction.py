from datetime import datetime, timezone
import uuid
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum, Numeric

from app.database import Base
from app.utils.enums import TransactionType, TransactionStatus

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    currency: Mapped[str] = mapped_column(String(50))
    usd_equivalent: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    
    # Deposit-specific
    crypto_address_sent_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    txn_hash: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    crypto_network: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Withdrawal-specific
    withdrawal_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    withdrawal_network: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Admin action
    admin_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # References
    investment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("investments.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by_id])
    investment: Mapped["Investment"] = relationship("Investment", back_populates="transactions")
