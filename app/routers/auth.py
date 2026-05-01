from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import Login, Register
from app.services.auth_service import register_user, authenticate_user
from app.dependencies import get_db
from app.services.email_service import send_welcome_email

router = APIRouter()

@router.post("/register")
async def register(user_in: Register, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, user_in)
    name = user.full_name if hasattr(user, "full_name") and user.full_name else user.username
    background_tasks.add_task(send_welcome_email, email=user.email, name=name)
    return {
        "success": True,
        "message": "User registered successfully",
        "data": {"id": str(user.id), "email": user.email}
    }

@router.post("/login")
async def login(login_data: Login, request: Request, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    access_token, refresh_token = await authenticate_user(db, login_data, ip_address, user_agent)
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }
