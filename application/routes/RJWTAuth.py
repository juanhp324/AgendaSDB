from flask import Blueprint, request, jsonify
import infrastructure.model.MAuth as MAuth
import domain.VAuth as VAuth
from infrastructure.core.jwt_auth import jwt_required, role_required, blacklist_token
from infrastructure.core.two_factor import TwoFactorAuth, TwoFactorSession, MAX_2FA_ATTEMPTS

bp = Blueprint('RJWTAuth', __name__)

@bp.route('/api/auth/login', methods=['POST'])
def jwt_login():
    """JWT login endpoint"""
    data = request.get_json(silent=True)
    
    # Check if this is 2FA verification
    if data and data.get('2fa_token') and data.get('temp_token'):
        return verify_jwt_2fa(data)
    
    # Regular login flow
    login = VAuth.loginValidator(is_json=True, payLoad=data)
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
        # Generate temporary token for 2FA verification
        import jwt
        from flask import current_app
        temp_token = jwt.encode(
            {
                'user_id': str(userData['_id']),
                'type': 'temp_2fa',
                'exp': jwt.datetime.datetime.utcnow() + jwt.datetime.timedelta(minutes=5)
            },
            current_app.secret_key,
            algorithm='HS256'
        )
        
        return jsonify({
            "success": True,
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "Se requiere verificación de dos factores"
        }), 200
    
    # Generate JWT tokens
    jwt_auth = current_app.jwt_auth
    tokens = jwt_auth.generate_tokens(userData)
    
    return jsonify({
        "success": True,
        "user_info": {
            "nombre": userData.get("nombre", "Usuario"),
            "avatar": userData.get("avatar", ""),
            "email": userData.get("email", ""),
            "rol": userData.get("rol", "user")
        },
        **tokens
    }), 200

def verify_jwt_2fa(data):
    """Verify 2FA token for JWT login"""
    temp_token = data.get('temp_token')
    token_2fa = data.get('2fa_token')
    
    if not temp_token or not token_2fa:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400
    
    # Verify temporary token
    import jwt
    from flask import current_app
    try:
        payload = jwt.decode(temp_token, current_app.secret_key, algorithms=['HS256'])
        if payload.get('type') != 'temp_2fa':
            return jsonify({"success": False, "message": "Token temporal inválido"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Token temporal inválido o expirado"}), 400
    
    user_id = payload['user_id']
    user = MAuth.getUserById(user_id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    
    # Verify 2FA token
    two_fa = TwoFactorAuth()
    if two_fa.verify_token(user['2fa_secret'], token_2fa):
        # Generate JWT tokens
        jwt_auth = current_app.jwt_auth
        tokens = jwt_auth.generate_tokens(user)
        
        return jsonify({
            "success": True,
            "user_info": {
                "nombre": user.get("nombre", "Usuario"),
                "avatar": user.get("avatar", ""),
                "email": user.get("email", ""),
                "rol": user.get("rol", "user")
            },
            **tokens
        }), 200
    else:
        return jsonify({"success": False, "message": "Token 2FA inválido"}), 401

@bp.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    data = request.get_json(silent=True)
    refresh_token = data.get('refresh_token') if data else None
    
    if not refresh_token:
        return jsonify({"message": "Refresh token is required"}), 400
    
    jwt_auth = current_app.jwt_auth
    new_tokens = jwt_auth.refresh_access_token(refresh_token)
    
    if not new_tokens:
        return jsonify({"message": "Invalid or expired refresh token"}), 401
    
    return jsonify({
        "success": True,
        **new_tokens
    }), 200

@bp.route('/api/auth/logout', methods=['POST'])
@jwt_required
def jwt_logout():
    """JWT logout endpoint"""
    token = request.headers.get('Authorization', '').split(' ')[-1]
    blacklist_token(token)
    
    return jsonify({
        "success": True,
        "message": "Sesión cerrada exitosamente"
    }), 200

@bp.route('/api/auth/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Get current user information"""
    user_id = request.current_user['user_id']
    user = MAuth.getUserById(user_id)
    
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    
    return jsonify({
        "success": True,
        "user": {
            "_id": str(user['_id']),
            "nombre": user.get('nombre', ''),
            "email": user.get('email', ''),
            "user": user.get('user', ''),
            "rol": user.get('rol', ''),
            "avatar": user.get('avatar', ''),
            "2fa_enabled": user.get('2fa_enabled', False)
        }
    }), 200

@bp.route('/api/auth/update_profile', methods=['PUT'])
@jwt_required
def update_profile_jwt():
    """Update user profile (JWT version)"""
    data = request.get_json(silent=True) or {}
    user_id = request.current_user['user_id']
    
    allowed = ['nombre', 'email', 'user', 'avatar']
    update_data = {k: v for k, v in data.items() if k in allowed and v}
    
    if not update_data:
        return jsonify({"success": False, "message": "Sin datos para actualizar"}), 400
    
    result = MAuth.updateUsuario(user_id, update_data)
    if result.modified_count > 0:
        return jsonify({"success": True, "message": "Perfil actualizado"})
    return jsonify({"success": False, "message": "No hubo cambios"}), 200

# Protected route examples
@bp.route('/api/protected', methods=['GET'])
@jwt_required
def protected_route():
    """Example protected route"""
    return jsonify({
        "message": "Acceso autorizado",
        "user": request.current_user
    }), 200

@bp.route('/api/admin-only', methods=['GET'])
@jwt_required
@role_required('admin', 'superadmin')
def admin_only_route():
    """Example admin-only route"""
    return jsonify({
        "message": "Acceso de administrador autorizado",
        "user": request.current_user
    }), 200
