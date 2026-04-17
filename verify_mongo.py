import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def test_connection():
    load_dotenv("src/.env")
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DATABASE_NAME")
    
    print(f"Connecting to: {url}")
    print(f"Database: {db_name}")
    
    client = AsyncIOMotorClient(url)
    try:
        # The ismaster command is cheap and does not require auth.
        await client[db_name].command("ping")
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
