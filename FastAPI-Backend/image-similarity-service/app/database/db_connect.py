# db/connection.py

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.database.models import fvector
from config import settings

MONGO_URL = settings.MONGO_URL
MONGO_DB = settings.MONGO_DB


# Connect to MongoDB and initialize Beanie models
async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB]
    await init_beanie(database=db, document_models=[fvector])
    print("--- Connected to MongoDB ---")
