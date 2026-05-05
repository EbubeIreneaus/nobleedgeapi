import asyncio
import sys
import os

# Add api path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import send_plain_email

async def main():
    try:
        await send_plain_email(
            email_to="alfredebube7@gmail.com",
            subject="Test Admin Email",
            body="<h1>Hello!</h1><p>This is a test email from Noble Edge ROI Admin Panel.</p>"
        )
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
