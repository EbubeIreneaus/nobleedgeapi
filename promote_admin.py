"""
Run this once to promote the ADMIN_EMAIL user to superadmin role.
Usage:  uv run python promote_admin.py
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.enums import UserRole
from sqlalchemy.future import select

ADMIN_EMAIL = "pojmercy2@gmail.com"

async def promote():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = result.scalars().first()
        if not user:
            print(f"[NOT FOUND] No user found with email: {ADMIN_EMAIL}")
            print("    Make sure to register an account first, then re-run this script.")
            return
        user.role = UserRole.superadmin
        user.is_active = True
        await db.commit()
        print(f"[OK] {ADMIN_EMAIL} has been promoted to superadmin!")

asyncio.run(promote())
