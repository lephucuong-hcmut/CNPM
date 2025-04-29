from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate():
    # Get MongoDB Atlas connection string from environment variable
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("Error: MONGODB_URL environment variable is not set")
        return

    try:
        # Connect to MongoDB Atlas
        client = AsyncIOMotorClient(mongodb_url)
        db = client.get_database()  # Get database from connection string
        
        # Get Booking collection
        booking_collection = db.Booking
        
        # Add qr_code field to all existing documents
        result = await booking_collection.update_many(
            {},  # Match all documents
            {"$set": {"qr_code": None}}  # Set qr_code to None for existing documents
        )
        
        print(f"Migration completed. Updated {result.modified_count} documents.")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        # Close connection
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate()) 