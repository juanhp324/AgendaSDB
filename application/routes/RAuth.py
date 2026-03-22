from flask import render_template, request, Blueprint, jsonify, redirect, url_for, session
import infrasture.model.MAuth as MAuth
import domain.VAuth as VAuth
from werkzeug.security import generate_password_hash

bp = Blueprint('RAuth', __name__)

@bp.route('/Login', methods=['GET'])
def show_login_form():
    return render_template('Auth/Login.html')

@bp.route('/Login', methods=['POST'])
def Login():
    data = request.get_json(silent=True)
    login = VAuth.loginValidator(is_json=request.is_json, payLoad=data)
    try:
        userData = login.validation()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"message": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 401

    session['user_id'] = str(userData['_id'])
    session['email'] = userData['email']
    session['rol'] = userData.get('rol', 'user')
    session['nombre'] = userData.get('nombre', 'Usuario')

    if data.get('remember'):
        session.permanent = True

    response = login.redirect_user()
    response["user_info"] = {
        "nombre": userData.get("nombre", "Usuario"),
        "avatar": userData.get("avatar", ""),
        "email": userData.get("email", "")
    }

    return jsonify(response), 200


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('RAuth.show_login_form'))

@bp.route('/get_perfil', methods=['GET'])
def get_perfil():
    user_id = session.get('user_id')
    user = MAuth.getUserById(user_id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    return jsonify({
        "success": True,
        "usuario": {
            "_id": str(user['_id']),
            "nombre": user.get('nombre', ''),
            "email": user.get('email', ''),
            "user": user.get('user', ''),
            "rol": user.get('rol', ''),
            "avatar": user.get('avatar', ''),
        }
    })

@bp.route('/update_perfil', methods=['PUT'])
def update_perfil():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    allowed = ['nombre', 'email', 'user', 'password', 'avatar']
    update_data = {k: v for k, v in data.items() if k in allowed and v}
    if not update_data:
        return jsonify({"success": False, "message": "Sin datos para actualizar"}), 400
    
    # Hashear contraseña si se está actualizando
    if 'password' in update_data:
        update_data['password'] = generate_password_hash(update_data['password'])
        
    result = MAuth.updateUsuario(user_id, update_data)
    # Actualizar sesión si cambió nombre
    if 'nombre' in update_data:
        session['nombre'] = update_data['nombre']
    if result.modified_count > 0:
        return jsonify({"success": True, "message": "Perfil actualizado"})
    return jsonify({"success": False, "message": "No hubo cambios"}), 200
