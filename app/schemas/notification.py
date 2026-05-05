from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.utils.enums import NotificationType

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType
    is_read: bool

class NotificationRead(NotificationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
