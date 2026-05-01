import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.email == 'pojmercy2@gmail.com'))
        users = r.scalars().all()
        print([(u.id, u.email, getattr(u.role, 'value', u.role)) for u in users])

asyncio.run(main())
