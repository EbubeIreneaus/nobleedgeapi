from datetime import datetime, timezone, timedelta
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.wallet import Wallet
from app.models.session import UserSession
from app.schemas.auth import Register, Login
from app.security.hashing import get_password_hash, verify_password
from app.security.jwt import create_access_token, create_refresh_token
import random
import string

def generate_referral_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def register_user(db: AsyncSession, user_in: Register) -> User:
    query = await db.execute(select(User).where((User.email == user_in.email) | (User.username == user_in.username)))
    if query.scalars().first():
        raise HTTPException(status_code=400, detail="Email or username already registered")

    referred_by_id = None
    if user_in.referral_code:
        ref_query = await db.execute(select(User).where(User.referral_code == user_in.referral_code))
        referrer = ref_query.scalars().first()
        if referrer:
            referred_by_id = referrer.id

    new_user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        referral_code=generate_referral_code(),
        referred_by_id=referred_by_id,
        email_verification_token=str(uuid.uuid4())
    )
    
    db.add(new_user)
    await db.flush() # flush to get new_user.id
    
    new_wallet = Wallet(user_id=new_user.id)
    db.add(new_wallet)
    
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

async def authenticate_user(db: AsyncSession, login_data: Login, ip_address: str | None = None, user_agent: str | None = None) -> tuple[str, str]:
    query = await db.execute(select(User).where(User.email == login_data.email))
    user = query.scalars().first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")
        
    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Create tokens
    access_token = create_access_token(data={"user_id": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"user_id": str(user.id)})
    
    # Save session
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    )
    db.add(session)
    await db.commit()
    
    return access_token, refresh_token
