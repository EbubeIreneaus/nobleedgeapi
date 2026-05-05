from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.database import Base
from app.utils.enums import UserRole, KYCStatus

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus), default=KYCStatus.none)
    profile_picture: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    email_verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False)
    investments: Mapped[list["Investment"]] = relationship("Investment", back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.user_id]", back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user")
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential
    referred_by: Mapped["User"] = relationship("User", remote_side=[id], back_populates="referrals_made")
    referrals_made: Mapped[list["User"]] = relationship("User", back_populates="referred_by")
