import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8000/api/v1/settings/deposit-addresses")
        print("Status:", resp.status_code)
        print("Response:", resp.text)

asyncio.run(main())
