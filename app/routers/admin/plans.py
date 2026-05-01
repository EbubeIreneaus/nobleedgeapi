from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_admin
from app.services.investment_service import sync_plans_from_json

router = APIRouter()

@router.post("/sync-json")
async def manual_sync_plans(db: AsyncSession = Depends(get_db)):
    await sync_plans_from_json(db)
    return {"success": True, "message": "Investment plans verified and synced"}
