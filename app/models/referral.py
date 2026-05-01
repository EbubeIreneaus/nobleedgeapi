from datetime import datetime, timezone
import uuid
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, Numeric, Float

from app.database import Base
from app.utils.enums import ReferralStatus

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    referrer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    referee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    bonus_percent: Mapped[float] = mapped_column(Float)
    
    status: Mapped[ReferralStatus] = mapped_column(Enum(ReferralStatus), default=ReferralStatus.pending)
    triggered_by_transaction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    
    credited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))

    # Relationships
    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id])
    referee: Mapped["User"] = relationship("User", foreign_keys=[referee_id])
    transaction: Mapped["Transaction"] = relationship("Transaction")
