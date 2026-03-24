from bson import ObjectId
from infrasture.db import get_database
from datetime import datetime
import re

def _get_col():
    db = get_database()
    return db["casas"]

def getAllCasas(query=None, tipo=None):
    col = _get_col()
    filtro = {}
    if query:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        filtro["$or"] = [{"nombre": pattern}, {"obras.ciudad": pattern}, {"obras.nombre_obra": pattern}]
    
    if tipo and tipo != 'todos':
        filtro["tipo"] = re.compile(f"^{tipo}$", re.IGNORECASE)
        
    # Optimización: Traer los campos necesarios. 
    # Incluimos 'obras' completo porque el frontend lo usa para los modales de detalle sin re-petición.
    proyeccion = {
        "nombre": 1, 
        "tipo": 1, 
        "obras": 1, 
        "historia": 1,
        "_id": 1
    }
    
    cursor = col.find(filtro, proyeccion).sort("_id", -1)
    result = list(cursor)
    cursor.close()
    return result

def getCasaById(casa_id):
    col = _get_col()
    return col.find_one({"_id": ObjectId(casa_id)})

def createCasa(data):
    col = _get_col()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    return col.insert_one(data)

def updateCasa(casa_id, data):
    col = _get_col()
    data["updated_at"] = datetime.utcnow()
    return col.update_one({"_id": ObjectId(casa_id)}, {"$set": data})

def deleteCasa(casa_id):
    col = _get_col()
    return col.delete_one({"_id": ObjectId(casa_id)})
