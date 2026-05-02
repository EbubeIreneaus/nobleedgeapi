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
        resp = await client.put(
            "http://localhost:8000/api/v1/settings/whatsapp",
            headers={"Authorization": f"Bearer {token}"},
            json={"value": "+1234567890"}
        )
        print("Status:", resp.status_code)
        print("Response:", resp.text)

asyncio.run(main())
