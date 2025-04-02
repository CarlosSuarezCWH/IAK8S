from pymongo import MongoClient
from app.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

def get_mongo_db():
    return db
