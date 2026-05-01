from datetime import datetime
from pydantic import BaseModel, Field
import uuid
from decimal import Decimal
from app.utils.enums import InvestmentStatus

class InvestmentBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency_used: str

class InvestmentCreate(InvestmentBase):
    plan_id: uuid.UUID

class InvestmentRead(InvestmentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    plan_id: uuid.UUID
    
    status: InvestmentStatus
    roi_percent: Decimal
    roi_cycle: str
    duration_days: int
    
    total_return_expected: Decimal
    total_return_paid: Decimal
    
    cycles_total: int
    cycles_completed: int
    
    next_roi_date: datetime
    started_at: datetime
    ends_at: datetime
    completed_at: datetime | None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
