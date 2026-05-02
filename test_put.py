import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.future import select
from app.security.jwt import create_access_token
from datetime import timedelta
import httpx

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.email == 'pojmercy2@gmail.com'))
        u = r.scalars().first()
        
        if not u:
            print("User not found!")
            return

        token = create_access_token(
            data={"user_id": str(u.id)}, expires_delta=timedelta(minutes=30)
        )
        print("Token:", token)
        
    # Now make the request
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            "http://localhost:8000/api/v1/settings/deposit-addresses",
            json={
                "btc_address": "testbtc",
                "eth_address": "testeth",
                "usdt_trc20_address": "testtrc",
                "usdt_erc20_address": "testerc"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status:", resp.status_code)
        print("Body:", resp.text)

asyncio.run(main())
