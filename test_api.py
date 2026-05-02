import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        # 1. Login
        resp = await client.post("http://localhost:8000/api/v1/auth/login", json={
            "email": "pojmercy2@gmail.com",
            "password": "yourpassword" # Assuming user knows password, but we don't.
        })
        print("Login status:", resp.status_code)
        # Actually I can't login without password.

asyncio.run(test_api())
