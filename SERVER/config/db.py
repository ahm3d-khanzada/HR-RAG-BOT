# filename: config/db.py
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "hr_chatbot")

client = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DB_NAME]
users_collection = db["users"]
