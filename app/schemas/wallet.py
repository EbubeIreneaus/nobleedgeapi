from datetime import datetime
from pydantic import BaseModel
import uuid
from decimal import Decimal

class WalletBase(BaseModel):
    pass

class WalletConnectRequest(BaseModel):
    address: str

class WalletRead(WalletBase):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    invested_balance: Decimal
    total_deposited: Decimal
    total_withdrawn: Decimal
    total_earned: Decimal
    referral_bonus: Decimal
    connected_wallet: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
