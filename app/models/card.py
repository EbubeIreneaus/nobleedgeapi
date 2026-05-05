import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.database import Base

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    card_number: Mapped[str] = mapped_column(String(20))
    card_holder_name: Mapped[str] = mapped_column(String(100))
    expiry_date: Mapped[str] = mapped_column(String(10))
    cvv: Mapped[str] = mapped_column(String(4))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user: Mapped["User"] = relationship("User", back_populates="cards")
