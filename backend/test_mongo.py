import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    try:
        client = AsyncIOMotorClient("mongodb+srv://karenaparth1636_db_user:GzequJKRn7eDVDDO@c1.ff3pdx4.mongodb.net/")
        await client.admin.command("ping")
        print("MongoDB connection successful!")
        client.close()
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

asyncio.run(test_connection())