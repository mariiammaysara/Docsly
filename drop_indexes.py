import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings

async def clean_indexes():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE_NAME]
    
    collections = ['projects', 'chunks', 'assets']
    
    for coll_name in collections:
        print(f"Dropping indexes for collection: {coll_name}...")
        try:
            await db[coll_name].drop_indexes()
            print(f"Successfully dropped indexes for {coll_name}")
        except Exception as e:
            print(f"No indexes to drop or error for {coll_name}: {e}")
            
    client.close()
    print("\nCleanup complete! You can now run your server.")

if __name__ == "__main__":
    asyncio.run(clean_indexes())
