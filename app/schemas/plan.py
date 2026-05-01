from datetime import datetime
from pydantic import BaseModel
import uuid
from decimal import Decimal
from app.utils.enums import ROICycle

class InvestmentPlanBase(BaseModel):
    name: str
    slug: str
    description: str
    min_amount: Decimal
    max_amount: Decimal | None
    roi_percent: Decimal
    roi_cycle: ROICycle
    duration_days: int
    total_return_percent: Decimal
    capital_returned: bool = True
    is_active: bool = True
    color: str
    icon: str | None = None
    features: list[str]

class InvestmentPlanCreate(InvestmentPlanBase):
    pass

class InvestmentPlanRead(InvestmentPlanBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvestmentPlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    roi_percent: Decimal | None = None
    roi_cycle: ROICycle | None = None
    duration_days: int | None = None
    total_return_percent: Decimal | None = None
    capital_returned: bool | None = None
    is_active: bool | None = None
    color: str | None = None
    icon: str | None = None
    features: list[str] | None = None
