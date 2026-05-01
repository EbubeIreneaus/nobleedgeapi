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
        token = create_access_token({"user_id": str(u.id)}, expires_delta=timedelta(minutes=10))
        
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:8000/api/v1/admin/dashboard/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status dashboard:", resp.status_code)
        print("Response dashboard:", resp.text)
        
        resp2 = await client.get(
            "http://localhost:8000/api/v1/admin/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status users:", resp2.status_code)
        print("Response users:", resp2.text)

asyncio.run(main())
