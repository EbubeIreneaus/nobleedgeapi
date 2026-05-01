from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.security.jwt import verify_token
from app.utils.enums import UserRole
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)

    user_id_str: str | None = payload.get("user_id")
    if user_id_str is None:
        raise credentials_exception

    # 🔥 CRITICAL FIX — convert string → UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")

    return user



async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Optional logic for email verification
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    
    with open("debug.txt", "a") as f:
        f.write(f"DEBUG: user email={current_user.email}, role={current_user.role}, role_val={role_val}, type(role_val)={type(role_val)}\n")
        
    if role_val not in ["admin", "superadmin"]:
        with open("debug.txt", "a") as f:
            f.write(f"DEBUG: role_val not in list. Raising 403.\n")
        raise HTTPException(status_code=403, detail=f"Not enough permissions: user={current_user.email}, role={role_val}")
    return current_user

require_admin = get_current_admin_user


async def require_superadmin(current_user: User = Depends(get_current_active_user)) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_val != "superadmin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def get_optional_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User | None:
    try:
        return await get_current_user(token, db)
    except Exception:
        return None
