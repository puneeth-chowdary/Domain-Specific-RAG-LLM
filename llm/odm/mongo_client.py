from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

_client = None
_database = None

def get_client():
    global _client
    if _client is None:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        _client = MongoClient(mongodb_uri)
    return _client

def get_database():
    global _database
    if _database is None:
        db_name = os.getenv('MONGODB_DB', 'article_warehouse')
        _database = get_client()[db_name]
    return _database