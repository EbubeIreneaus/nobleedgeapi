import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.email == 'pojmercy2@gmail.com'))
        u = r.scalars().first()
        if u:
            print(f"Role: {u.role}")
        else:
            print("User not found")

asyncio.run(main())
