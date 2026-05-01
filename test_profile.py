import asyncio
import httpx
from datetime import timedelta
from app.security.jwt import create_access_token
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.email == 'pojmercy2@gmail.com'))
        u = r.scalars().first()
        if not u:
            print("User not found in DB")
            return
        
        # generate token
        token = create_access_token({"user_id": str(u.id)}, expires_delta=timedelta(minutes=10))
        
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:8000/api/v1/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status:", resp.status_code)
        print("JSON:", resp.json())

asyncio.run(main())
