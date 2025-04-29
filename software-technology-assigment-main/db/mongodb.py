from motor.motor_asyncio import AsyncIOMotorClient


class DataBase:
    client: AsyncIOMotorClient = None
    db: None = None

    @classmethod
    def init(cls, uri: str, dbname: str):
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[dbname] 


db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return db.client
