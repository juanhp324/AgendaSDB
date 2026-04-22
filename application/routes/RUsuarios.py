from flask import render_template, request, Blueprint, jsonify, session
import infrastructure.model.MAuth as MAuth
from domain.VPermisos import requiere_permiso, tiene_permiso
from werkzeug.security import generate_password_hash

bp = Blueprint('RUsuarios', __name__)

@bp.route('/usuarios')
def usuarios():
    rol = session.get('rol', 'user')
    if rol not in ['admin', 'superadmin']:
        return jsonify({"success": False, "message": "Acceso denegado"}), 403
    return render_template('Usuarios/Usuarios.html', active_page='usuarios')

@bp.route('/get_usuarios', methods=['GET'])
@requiere_permiso('usuarios', 'ver')
def get_usuarios():
    try:
        all_users = MAuth.getAllUsers()
        rol_actual = session.get('rol')
        result = []
        for u in all_users:
            # admin no ve admins ni superadmins
            if rol_actual == 'admin' and u.get('rol') in ['admin', 'superadmin']:
                continue
            result.append({
                '_id': str(u['_id']),
                'nombre': u.get('nombre', ''),
                'email': u.get('email', ''),
                'user': u.get('user', ''),
                'rol': u.get('rol', ''),
                'avatar': u.get('avatar', ''),
                'activo': u.get('activo', True),
                '2fa_enabled': u.get('2fa_enabled', False),
            })
        return jsonify({"success": True, "usuarios": result})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/create_usuario', methods=['POST'])
@requiere_permiso('usuarios', 'crear')
def create_usuario():
    try:
        data = request.get_json(silent=True) or {}
        required = ['nombre', 'email', 'user', 'password', 'rol']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "message": f"Campo '{field}' es obligatorio"}), 400
        # solo superadmin puede crear admin/superadmin
        if data['rol'] in ['admin', 'superadmin'] and session.get('rol') != 'superadmin':
            return jsonify({"success": False, "message": "Solo superadmin puede crear admins"}), 403
        
        # Hashear contraseña
        data['password'] = generate_password_hash(data['password'])
        
        result = MAuth.createUsuario(data)
        return jsonify({"success": True, "message": "Usuario creado", "usuario_id": str(result.inserted_id)}), 201
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/update_usuario/<user_id>', methods=['PUT'])
@requiere_permiso('usuarios', 'editar')
def update_usuario(user_id):
    try:
        data = request.get_json(silent=True) or {}
        target_user = MAuth.getUserById(user_id)
        if not target_user:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
        rol_actual = session.get('rol')
        # admin solo puede editar usuarios con rol 'user'
        if rol_actual == 'admin' and target_user.get('rol') in ['admin', 'superadmin']:
            return jsonify({"success": False, "message": "No puedes editar este usuario"}), 403
        allowed = ['nombre', 'email', 'user', 'password', 'rol', 'avatar', 'activo']
        update_data = {k: v for k, v in data.items() if k in allowed and v != ''}
        
        # Impedir que un usuario se cambie el rol a sí mismo
        if str(user_id) == session.get('user_id') and 'rol' in update_data:
            del update_data['rol']
            
        # impedir que admin cambie rol a admin/superadmin
        # Hashear contraseña si se está actualizando
        if 'password' in update_data:
            update_data['password'] = generate_password_hash(update_data['password'])
            
        result = MAuth.updateUsuario(user_id, update_data)
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Usuario actualizado"})
        return jsonify({"success": False, "message": "No hubo cambios"}), 200
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/disable_2fa_usuario/<user_id>', methods=['POST'])
def disable_2fa_usuario(user_id):
    rol_actual = session.get('rol', '')
    if rol_actual not in ['admin', 'superadmin']:
        return jsonify({"success": False, "message": "Acceso denegado"}), 403
    try:
        target = MAuth.getUserById(user_id)
        if not target:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
        if not target.get('2fa_enabled', False):
            return jsonify({"success": False, "message": "El usuario no tiene 2FA activo"}), 400
        MAuth.update2FA(user_id, False)
        return jsonify({"success": True, "message": "2FA desactivado para el usuario"})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/delete_usuario/<user_id>', methods=['DELETE'])
@requiere_permiso('usuarios', 'eliminar')
def delete_usuario(user_id):
    try:
        # Solo superadmin puede llegar aquí por el permiso
        if str(user_id) == session.get('user_id'):
            return jsonify({"success": False, "message": "No puedes eliminarte a ti mismo"}), 400
        result = MAuth.deleteUsuario(user_id)
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Usuario eliminado"})
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
