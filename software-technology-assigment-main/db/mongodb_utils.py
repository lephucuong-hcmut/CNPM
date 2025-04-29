from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import config
from db.mongodb import db
from models.booking import  Booking
from models.room import Room
from models.user import User


async def connect_to_mongo(
    mongo_uri: str = config.MONGO_URL, dbname: str = config.DATABASE_NAME
):
    print("Connecting to database...")
    db.client = AsyncIOMotorClient(
        str(mongo_uri),
        maxPoolSize=config.MAX_CONNECTIONS_COUNT,
        minPoolSize=config.MIN_CONNECTIONS_COUNT,
    )
    db.db = db.client[dbname]
    document_models = [
        User,
        Room,
        Booking
    ]
    await init_beanie(
        db.db,
        document_models=document_models,
    )
    db_collections = await db.db.list_collection_names()
    for document in document_models:
        document_name = document.Settings.name
        if document_name not in db_collections:
            await db.db.create_collection(document_name)
            print(f"Created {document_name}")
    print("Connected to database！")
    return document_models


async def close_mongo_connection():
    print("Closing database connection...")

    if db.client:
        db.client.close()
        db.client = None 
        db.db = None  
        print("Database connection closed!")
    else:
        print("Database connection is already closed or was never initialized.")