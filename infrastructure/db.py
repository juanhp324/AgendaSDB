from pymongo import MongoClient
import threading
import os

from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "AgendaSDB")

if not MONGODB_URI:
    MONGODB_URI = "mongodb://localhost:27017/?directConnection=true"


CONNECTION_CONFIG = {
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 5000,
    "socketTimeoutMS": 5000,
    "maxPoolSize": 10,  # Reduced from 50 to optimize resources
    "minPoolSize": 2,   # Reduced from 10
    "maxIdleTimeMS": 30000,
    "retryWrites": True,
    "retryReads": True,
    "w": "majority",
    "journal": True,
    "waitQueueTimeoutMS": 5000
}

from infrastructure.core.safety import CircuitBreaker, ServiceUnavailableError

_client = None
_db = None
_lock = threading.Lock()

# Circuit Breaker para proteger la conexión a la base de datos
db_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

@db_circuit_breaker
def get_database():
    """Lazy initialization of MongoDB connection"""
    global _client, _db

    if _client is not None and _db is not None:
        return _db

    with _lock:
        if _client is not None and _db is not None:
            return _db
        try:
            _client = MongoClient(MONGODB_URI, **CONNECTION_CONFIG)
            # Test connection with timeout
            _client.admin.command('ping')
            _db = _client[DATABASE_NAME]
            print(f"[OK] Conexion exitosa a MongoDB: {DATABASE_NAME}")
        except Exception as e:
            print(f"[ERROR] Error al conectar a MongoDB: {e}")
            _client = None
            _db = None
            raise ServiceUnavailableError(f"Base de datos no disponible: {str(e)}")

    return _db

def close_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        print("[OK] Conexion a MongoDB cerrada")

def is_database_connected():
    """Check if database is connected without triggering connection"""
    return _client is not None and _db is not None

# Lazy initialization - don't connect on import
db = None  # Will be initialized when first needed
