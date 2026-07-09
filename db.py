from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = None
db = None

def connect():
    global client, db
    if client is not None:
        return True
    try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        db = client[DB_NAME]
        return True
    except Exception:
        client = None
        db = None
        return False

def disconnect():
    global client
    if client:
        client.close()
        client = None

def get_collection(name):
    if db is None:
        raise RuntimeError("Base de données non connectée")
    return db[name]
