from datetime import datetime, timezone
import uuid
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Enum, Numeric, JSON

from app.database import Base
from app.utils.enums import ROICycle

class InvestmentPlan(Base):
    __tablename__ = "investment_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(1000))
    min_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    roi_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    roi_cycle: Mapped[ROICycle] = mapped_column(Enum(ROICycle))
    duration_days: Mapped[int] = mapped_column()
    total_return_percent: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    capital_returned: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(20))
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    features: Mapped[list[str]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    )

    # Relationships
    investments: Mapped[list["Investment"]] = relationship("Investment", back_populates="plan")
