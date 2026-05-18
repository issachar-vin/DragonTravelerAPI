from pymongo import MongoClient

from config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    return get_client()[settings.db_name]
