import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
async def migrate():
    # Connect to MongoDB
    load_dotenv()

    print("DEBUG MONGODB_URL:", os.getenv("MONGODB_URL"))
    mongodb_url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.cnpm
    
    # Get Booking collection
    booking_collection = db.Booking
    
    # Add qr_code field to all existing documents
    result = await booking_collection.update_many(
        {},  # Match all documents
        {"$set": {"qr_code": None}}  # Set qr_code to None for existing documents
    )
    
    print(f"Migration completed. Updated {result.modified_count} documents.")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
    