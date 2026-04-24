from datetime import datetime, timezone
import uuid
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum, Numeric

from app.database import Base
from app.utils.enums import InvestmentStatus

class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investment_plans.id"))
    
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency_used: Mapped[str] = mapped_column(String(50))
    
    status: Mapped[InvestmentStatus] = mapped_column(Enum(InvestmentStatus), default=InvestmentStatus.active)
    
    # Snapshots
    roi_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    roi_cycle: Mapped[str] = mapped_column(String(50))
    duration_days: Mapped[int] = mapped_column()
    
    total_return_expected: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_return_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal('0'))
    
    cycles_total: Mapped[int] = mapped_column()
    cycles_completed: Mapped[int] = mapped_column(default=0)
    
    next_roi_date: Mapped[datetime] = mapped_column(DateTime)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="investments")
    plan: Mapped["InvestmentPlan"] = relationship("InvestmentPlan", back_populates="investments")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="investment")
