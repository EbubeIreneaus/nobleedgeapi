from datetime import datetime
from pydantic import BaseModel, Field
import uuid
from decimal import Decimal
from app.utils.enums import TransactionType, TransactionStatus

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str

class TransactionCreate(TransactionBase):
    type: TransactionType
    crypto_address_sent_to: str | None = None
    txn_hash: str | None = None
    crypto_network: str | None = None
    withdrawal_address: str | None = None
    withdrawal_network: str | None = None

class TransactionRead(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    type: TransactionType
    status: TransactionStatus
    usd_equivalent: Decimal | None
    
    crypto_address_sent_to: str | None
    txn_hash: str | None
    crypto_network: str | None
    
    withdrawal_address: str | None
    withdrawal_network: str | None
    
    admin_note: str | None
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    
    investment_id: uuid.UUID | None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    status: TransactionStatus
    usd_equivalent: Decimal | None = None
    admin_note: str | None = None
