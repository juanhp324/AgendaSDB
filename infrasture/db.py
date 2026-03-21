from pymongo import MongoClient
import threading
import os

from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "AgendaSDB")

if not MONGODB_URI:
    print("[WARNING] MONGODB_URI no definida en .env. Usando localhost por defecto.")
    MONGODB_URI = "mongodb://root:Servextex5252-@localhost:27017/?directConnection=true&readPreference=primary&replicaSet=rs0"


CONNECTION_CONFIG = {
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 5000,
    "socketTimeoutMS": 5000,
    "maxPoolSize": 50,
    "minPoolSize": 10,
    "maxIdleTimeMS": 30000,
    "retryWrites": True,
    "retryReads": True,
    "w": "majority",
    "journal": True,
    "waitQueueTimeoutMS": 5000
}

_client = None
_db = None
_lock = threading.Lock()

def get_database():
    global _client, _db

    if _client is not None and _db is not None:
        return _db

    with _lock:
        if _client is not None and _db is not None:
            return _db
        try:
            _client = MongoClient(MONGODB_URI, **CONNECTION_CONFIG)
            _client.admin.command('ping')
            _db = _client[DATABASE_NAME]
            print(f"[OK] Conexion exitosa a MongoDB: {DATABASE_NAME}")
        except Exception as e:
            print(f"[ERROR] Error al conectar a MongoDB: {e}")
            _client = None
            _db = None
            raise

    return _db

def close_connection():
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        print("[OK] Conexion a MongoDB cerrada")

db = get_database()
