from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = None
db = None

def connect():
    global client, db
    try:
        if client is None:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            db.command("ping")
        return True
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
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
