from infrasture.db import get_database
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

def _get_col():
    db = get_database()
    return db["usuarios"]

def getUserByEmail(email):
    col = _get_col()
    return col.find_one({"email": email}, {"email": 1, "password": 1, "rol": 1, "nombre": 1, "user": 1, "avatar": 1})

def getUserById(user_id):
    col = _get_col()
    return col.find_one({"_id": ObjectId(user_id)})

def getAllUsers():
    col = _get_col()
    cursor = col.find({}, {"password": 0})
    result = list(cursor)
    cursor.close()
    return result

def updateUsuario(user_id, data):
    col = _get_col()
    return col.update_one({"_id": ObjectId(user_id)}, {"$set": data})

def deleteUsuario(user_id):
    col = _get_col()
    return col.delete_one({"_id": ObjectId(user_id)})

def createUsuario(data):
    col = _get_col()
    return col.insert_one(data)
