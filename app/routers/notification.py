from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from uuid import UUID

from app.database import AsyncSessionLocal
from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationRead

router = APIRouter(tags=["notifications"])

@router.get("/", response_model=dict)
async def get_my_notifications(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    query = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    notifications = query.scalars().all()
    
    return {
        "success": True,
        "data": notifications
    }

@router.patch("/{id}/read", response_model=dict)
async def mark_notification_read(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = await db.execute(
        select(Notification)
        .where(Notification.id == id, Notification.user_id == current_user.id)
    )
    notification = query.scalars().first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await db.commit()
    
    return {
        "success": True,
        "message": "Notification marked as read"
    }

@router.patch("/read-all", response_model=dict)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    notifications = query.scalars().all()
    
    for notification in notifications:
        notification.is_read = True
        
    await db.commit()
    
    return {
        "success": True,
        "message": "All notifications marked as read"
    }
