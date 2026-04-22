from infrastructure.db import get_database
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

def _get_col():
    db = get_database()
    return db["usuarios"]

def getUserByEmail(email):
    col = _get_col()
    return col.find_one({"email": email}, {"email": 1, "password": 1, "rol": 1, "nombre": 1, "user": 1, "avatar": 1, "activo": 1, "2fa_enabled": 1, "2fa_secret": 1})

def getUserById(user_id):
    col = _get_col()
    return col.find_one({"_id": ObjectId(user_id)}, {"password": 0, "2fa_secret": 0})

def getAllUsers():
    col = _get_col()
    cursor = col.find({}, {"password": 0, "2fa_secret": 0})
    result = list(cursor)
    cursor.close()
    return result

def updateUsuario(user_id, data):
    """
    Update user with field validation and projection
    
    Args:
        user_id: User ID string
        data: Dictionary with fields to update
        
    Returns:
        MongoDB UpdateResult
        
    Raises:
        ValueError: If invalid fields are provided
    """
    # Whitelist of allowed fields for update
    allowed_fields = {
        'nombre', 'email', 'user', 'password', 'avatar', 'rol', 'activo', '2fa_enabled'
    }
    
    # Filter data to only allowed fields
    filtered_data = {}
    for field, value in data.items():
        if field in allowed_fields and value is not None:
            # Hash password if being updated
            if field == 'password':
                filtered_data[field] = generate_password_hash(value)
            else:
                filtered_data[field] = value
    
    if not filtered_data:
        raise ValueError("No valid fields provided for update")
    
    col = _get_col()
    return col.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": filtered_data}
    )

def update2FA(user_id, enabled, secret=None):
    """Enable or disable 2FA for a user"""
    col = _get_col()
    update = {"$set": {"2fa_enabled": enabled}}
    if enabled and secret is not None:
        update["$set"]["2fa_secret"] = secret
    elif not enabled:
        update["$unset"] = {"2fa_secret": ""}
    return col.update_one({"_id": ObjectId(user_id)}, update)

def deleteUsuario(user_id):
    col = _get_col()
    return col.delete_one({"_id": ObjectId(user_id)})

def createUsuario(data):
    col = _get_col()
    return col.insert_one(data)
