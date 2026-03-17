from flask import session, jsonify
from functools import wraps

PERMISOS = {
    'superadmin': {
        'casas': ['ver', 'crear', 'editar', 'eliminar'],
        'usuarios': ['ver', 'crear', 'editar', 'eliminar'],
    },
    'admin': {
        'casas': ['ver', 'crear', 'editar', 'eliminar'],
        'usuarios': ['ver', 'editar'],   # solo puede editar rol 'user'
    },
    'user': {
        'casas': ['ver'],
        'usuarios': [],
    }
}

def tiene_permiso(modulo, accion):
    rol = session.get('rol', 'user')
    return accion in PERMISOS.get(rol, {}).get(modulo, [])

def requiere_permiso(modulo, accion):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not tiene_permiso(modulo, accion):
                return jsonify({
                    "success": False,
                    "message": "No tienes permisos para realizar esta acción"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def obtener_permisos_usuario():
    rol = session.get('rol', 'user')
    return PERMISOS.get(rol, {})

def es_rol(rol_requerido):
    from flask import redirect, url_for
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rol_actual = session.get('rol', 'user')
            roles = rol_requerido if isinstance(rol_requerido, list) else [rol_requerido]
            if rol_actual not in roles:
                return jsonify({"success": False, "message": "Acceso denegado"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
