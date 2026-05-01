from datetime import datetime
from pydantic import BaseModel
import uuid
from decimal import Decimal
from app.utils.enums import ReferralStatus

class ReferralBase(BaseModel):
    pass

class ReferralRead(ReferralBase):
    id: uuid.UUID
    referrer_id: uuid.UUID
    referee_id: uuid.UUID
    
    bonus_amount: Decimal
    bonus_percent: float
    
    status: ReferralStatus
    triggered_by_transaction_id: uuid.UUID | None
    
    credited_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
