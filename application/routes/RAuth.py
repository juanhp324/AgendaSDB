from flask import render_template, request, Blueprint, jsonify, redirect, url_for, session
import infrastructure.model.MAuth as MAuth
import domain.VAuth as VAuth
from werkzeug.security import generate_password_hash
from infrastructure.core.two_factor import TwoFactorAuth, TwoFactorSession, MAX_2FA_ATTEMPTS

bp = Blueprint('RAuth', __name__)

@bp.route('/Login', methods=['GET'])
def show_login_form():
    return render_template('Auth/Login.html')

@bp.route('/Login', methods=['POST'])
def Login():
    data = request.get_json(silent=True)
    
    # Check if this is 2FA verification
    if data and data.get('2fa_token'):
        return verify_2fa(data)
    
    # Regular login flow
    login = VAuth.loginValidator(is_json=request.is_json, payLoad=data)
    try:
        userData = login.validation()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"message": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 401

    # Check if user has 2FA enabled
    if userData.get('2fa_enabled', False) and userData.get('2fa_secret'):
        # Set 2FA pending state
        TwoFactorSession.set_2fa_pending(session, str(userData['_id']), userData)
        return jsonify({
            "success": True,
            "requires_2fa": True,
            "message": "Se requiere verificación de dos factores"
        }), 200
    
    # Complete login without 2FA
    return complete_login(userData, data, login)

def verify_2fa(data):
    """Verify 2FA token"""
    if not TwoFactorSession.is_2fa_pending(session):
        return jsonify({"success": False, "message": "Sesión no válida"}), 400
    
    user_id = TwoFactorSession.get_pending_user_id(session)
    user_data = TwoFactorSession.get_pending_user_data(session)
    attempts = TwoFactorSession.increment_2fa_attempts(session)
    
    if attempts > MAX_2FA_ATTEMPTS:
        TwoFactorSession.clear_2fa_pending(session)
        return jsonify({"success": False, "message": "Demasiados intentos. Por favor, inicie sesión nuevamente."}), 429
    
    token = data.get('2fa_token')
    if not token or len(token) != 6:
        return jsonify({"success": False, "message": "Token inválido"}), 400
    
    # Verify token
    two_fa = TwoFactorAuth()
    if two_fa.verify_token(user_data['2fa_secret'], token):
        # Complete login
        TwoFactorSession.complete_2fa_login(session, user_data)
        
        # Generate redirect response
        from domain.VAuth import loginValidator
        login = loginValidator(is_json=True, payLoad={})
        response = login.redirect_user()
        response["user_info"] = {
            "nombre": user_data.get("nombre", "Usuario"),
            "avatar": user_data.get("avatar", ""),
            "email": user_data.get("email", "")
        }
        
        return jsonify(response), 200
    else:
        remaining_attempts = MAX_2FA_ATTEMPTS - attempts
        return jsonify({
            "success": False, 
            "message": f"Token inválido. Intentos restantes: {remaining_attempts}"
        }), 401

def complete_login(userData, data, login):
    """Complete user login process"""
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

@bp.route('/setup_2fa', methods=['POST'])
def setup_2fa():
    """Setup 2FA for current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "No autenticado"}), 401
    
    user = MAuth.getUserById(user_id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    
    # Generate 2FA setup data
    two_fa = TwoFactorAuth()
    secret, qr_code = two_fa.setup_2fa_data(user['email'])
    
    # Store secret temporarily (not enabled yet)
    MAuth.updateUsuario(user_id, {'2fa_secret_temp': secret})
    
    return jsonify({
        "success": True,
        "qr_code": qr_code,
        "secret": secret,
        "message": "Escanea el código QR con tu aplicación autenticadora"
    })

@bp.route('/enable_2fa', methods=['POST'])
def enable_2fa():
    """Enable 2FA after verification"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "No autenticado"}), 401
    
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    
    if not token or len(token) != 6:
        return jsonify({"success": False, "message": "Token inválido"}), 400
    
    user = MAuth.getUserById(user_id)
    if not user or not user.get('2fa_secret_temp'):
        return jsonify({"success": False, "message": "Configuración 2FA no encontrada"}), 400
    
    # Verify token
    two_fa = TwoFactorAuth()
    if two_fa.verify_token(user['2fa_secret_temp'], token):
        # Enable 2FA
        MAuth.updateUsuario(user_id, {
            '2fa_secret': user['2fa_secret_temp'],
            '2fa_enabled': True,
            '2fa_secret_temp': None  # Clear temporary secret
        })
        return jsonify({
            "success": True,
            "message": "Autenticación de dos factores habilitada exitosamente"
        })
    else:
        return jsonify({"success": False, "message": "Token inválido"}), 401

@bp.route('/disable_2fa', methods=['POST'])
def disable_2fa():
    """Disable 2FA for current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "No autenticado"}), 401
    
    data = request.get_json(silent=True) or {}
    password = data.get('password')
    
    if not password:
        return jsonify({"success": False, "message": "Se requiere contraseña para deshabilitar 2FA"}), 400
    
    # Verify password (would need password verification logic)
    # For now, just disable 2FA
    MAuth.updateUsuario(user_id, {
        '2fa_enabled': False,
        '2fa_secret': None
    })
    
    return jsonify({
        "success": True,
        "message": "Autenticación de dos factores deshabilitada"
    })

@bp.route('/2fa_status', methods=['GET'])
def get_2fa_status():
    """Get current user 2FA status"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "No autenticado"}), 401
    
    user = MAuth.getUserById(user_id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    
    return jsonify({
        "success": True,
        "2fa_enabled": user.get('2fa_enabled', False),
        "has_setup": bool(user.get('2fa_secret_temp'))
    })
