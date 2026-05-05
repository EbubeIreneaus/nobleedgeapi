from pydantic import BaseModel, Field, constr
from uuid import UUID
from datetime import datetime

class CardBase(BaseModel):
    card_number: constr(min_length=13, max_length=19) # type: ignore
    card_holder_name: constr(min_length=2, max_length=100) # type: ignore
    expiry_date: constr(pattern=r"^(0[1-9]|1[0-2])\/?([0-9]{2})$") # type: ignore
    cvv: constr(min_length=3, max_length=4) # type: ignore

class CardCreate(CardBase):
    pass

class CardResponse(CardBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    # Hide the full card number in the response for security, just showing last 4
    masked_card_number: str | None = None

    class Config:
        from_attributes = True
