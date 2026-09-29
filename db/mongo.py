import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/axc_music_bot")

class MongoDB:
    _instance = None
    client: AsyncIOMotorClient = None
    db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = AsyncIOMotorClient(MONGO_URI)
            cls._instance.db = cls._instance.client.get_default_database("axc_music_bot")
            print(f"🍃 MongoDB Client initialized.")
        return cls._instance

    @classmethod
    def get_collection(cls, collection_name: str):
        if cls._instance is None:
            cls()
        return cls._instance.db[collection_name]

mongodb = MongoDB()

# Helper Collections
prefixes_col = mongodb.get_collection("prefixes")
blacklist_col = mongodb.get_collection("blacklist")
ignore_col = mongodb.get_collection("ignore")
topcheck_col = mongodb.get_collection("topcheck")
guild_configs_col = mongodb.get_collection("guild_configs")
antinuke_col = mongodb.get_collection("antinuke")
automod_col = mongodb.get_collection("automod")
warns_col = mongodb.get_collection("warns")
tickets_col = mongodb.get_collection("tickets")
leveling_col = mongodb.get_collection("leveling")
afk_col = mongodb.get_collection("afk")
giveaways_col = mongodb.get_collection("giveaways")
autorole_col = mongodb.get_collection("autorole")
welcome_col = mongodb.get_collection("welcome")
customroles_col = mongodb.get_collection("customroles")
