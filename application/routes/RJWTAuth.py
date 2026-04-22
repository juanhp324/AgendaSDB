from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash, current_app
import infrastructure.model.MAuth as MAuth
import domain.VAuth as VAuth
from infrastructure.core.jwt_auth import jwt_required, role_required, blacklist_token
from infrastructure.core.two_factor import TwoFactorAuth, TwoFactorSession, MAX_2FA_ATTEMPTS
from infrastructure.core.encryption import get_encryption_manager
from werkzeug.security import check_password_hash
from infrastructure.core.safety import SecureLogger

bp = Blueprint('RJWTAuth', __name__)

@bp.route('/Login', methods=['GET'])
def show_login_form():
    """Mostrar formulario de login"""
    return render_template('Auth/Login.html')

@bp.route('/Login', methods=['POST'])
def login():
    """Login endpoint - maneja tanto formularios web como JSON"""
    # Rate limiting
    from infrastructure.core.redis_rate_limiter import get_rate_limiter
    limiter = get_rate_limiter(requests=5, window=60)  # 5 requests per minute
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    if not limiter.is_allowed(client_ip):
        if request.is_json:
            return jsonify({"message": "Too many login attempts. Please try again later."}), 429
        else:
            return render_template('Auth/Login.html', error="Demasiados intentos. Espera un momento.")
    
    # Obtener datos según el tipo de request
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = {
            'email': request.form.get('email', ''),
            'password': request.form.get('password', ''),
            'remember': request.form.get('remember') == 'on'
        }
    
    # Check if this is 2FA verification
    if data and data.get('2fa_token') and data.get('temp_token'):
        return verify_2fa(data)
    
    # Regular login flow
    login = VAuth.loginValidator(is_json=request.is_json, payLoad=data)
    try:
        userData = login.validation()
    except ValueError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 400
        else:
            return render_template('Auth/Login.html', error=str(exc))
    except LookupError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 404
        else:
            return render_template('Auth/Login.html', error=str(exc))
    except PermissionError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 401
        else:
            return render_template('Auth/Login.html', error=str(exc))

    # Check if user has 2FA enabled
    if userData.get('2fa_enabled', False) and userData.get('2fa_secret'):
        # Generate temporary token for 2FA verification
        import jwt as pyjwt
        from datetime import datetime, timedelta
        temp_token = pyjwt.encode(
            {
                'user_id': str(userData['_id']),
                'type': 'temp_2fa',
                'exp': datetime.utcnow() + timedelta(minutes=5)
            },
            current_app.secret_key,
            algorithm='HS256'
        )
        
        # Set 2FA pending state
        TwoFactorSession.set_2fa_pending(request.session, userData)
        
        if request.is_json:
            return jsonify({
                "success": True,
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "Se requiere verificación de dos factores"
            })
        else:
            # Para formulario web, mostrar página de 2FA
            return render_template('Auth/2FA.html', temp_token=temp_token, email=data.get('email'))
    
    # Generate JWT tokens
    try:
        tokens = current_app.jwt_auth.generate_tokens(userData)
    except Exception as e:
        SecureLogger.safe_log(f"Error generando tokens JWT: {str(e)}")
        return jsonify({"success": False, "message": f"Error al generar sesión: {str(e)}"}), 500
    
    # Set session for gateway compatibility
    session['user_id'] = str(userData['_id'])
    session['nombre'] = userData.get('nombre', 'Usuario')
    session['rol'] = userData.get('rol', 'user')
    session['email'] = userData.get('email', '')
    session.permanent = True
    
    if request.is_json:
        return jsonify({
            "success": True,
            "access_token": tokens['access_token'],
            "refresh_token": tokens['refresh_token'],
            "token_type": "Bearer",
            "expires_in": tokens['expires_in'],
            "redirect": "/inicio",
            "user_info": {
                "nombre": userData.get("nombre", "Usuario"),
                "avatar": userData.get("avatar", ""),
                "email": userData.get("email", "")
            }
        })
    else:
        # Para formulario web, guardar tokens y redirigir
        response = redirect('/inicio')
        
        # Set JWT tokens as cookies for web
        response.set_cookie('access_token', tokens['access_token'], httponly=True, secure=True)
        response.set_cookie('refresh_token', tokens['refresh_token'], httponly=True, secure=True)
        
        return response
    
@bp.route('/logout')
def logout():
    """Cerrar sesión para entorno web"""
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('RJWTAuth.show_login_form'))

@bp.route('/api/auth/login', methods=['POST'])
def jwt_login():
    """JWT login endpoint"""
    # Rate limiting for login endpoint
    from infrastructure.core.redis_rate_limiter import get_rate_limiter
    limiter = get_rate_limiter(requests=5, window=60)  # 5 requests per minute
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    if not limiter.is_allowed(client_ip):
        return jsonify({"message": "Too many login attempts. Please try again later."}), 429
    
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
        import jwt as pyjwt
        from datetime import datetime, timedelta
        temp_token = pyjwt.encode(
            {
                'user_id': str(userData['_id']),
                'type': 'temp_2fa',
                'exp': datetime.utcnow() + timedelta(minutes=5)
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


def verify_2fa(data):
    """Verificar 2FA para flujo web"""
    temp_token = data.get('temp_token')
    token_2fa = data.get('2fa_token')
    
    if not temp_token or not token_2fa:
        return render_template('Auth/Login.html', error="Datos de 2FA incompletos.")
        
    import jwt
    try:
        # Use current_app.secret_key safely
        payload = jwt.decode(temp_token, current_app.secret_key, algorithms=['HS256'])
        if payload.get('type') != 'temp_2fa':
            return render_template('Auth/Login.html', error="Token 2FA inválido.")
    except jwt.InvalidTokenError:
        return render_template('Auth/Login.html', error="Token 2FA expirado o inválido.")
        
    user_id = payload['user_id']
    user = MAuth.getUserById(user_id)
    
    if not user:
        return render_template('Auth/Login.html', error="Usuario no encontrado.")
        
    two_fa = TwoFactorAuth()
    # Decrypt secret before verifying
    from infrastructure.core.encryption import get_encryption_manager
    encryption_manager = get_encryption_manager()
    
    try:
        encrypted_secret = user.get('2fa_secret')
        if not encrypted_secret:
             return render_template('Auth/Login.html', error="2FA no está configurado para este usuario.")
        secret = encryption_manager.decrypt(encrypted_secret)
    except Exception:
        return render_template('Auth/Login.html', error="Error al procesar la seguridad 2FA.")

    if two_fa.verify_token(secret, token_2fa):
        # Complete login using session management
        TwoFactorSession.complete_2fa_login(session, user)
        return redirect(url_for('RInicio.inicio'))
    else:
        # Increment attempts and check for lockout
        attempts = TwoFactorSession.increment_2fa_attempts(session)
        if attempts >= MAX_2FA_ATTEMPTS:
            TwoFactorSession.clear_2fa_pending(session)
            return render_template('Auth/Login.html', error="Demasiados intentos fallidos de 2FA. Inicia sesión de nuevo.")
            
        return render_template('Auth/2FA.html', 
                             temp_token=temp_token, 
                             email=user.get('email'), 
                             error=f"Código 2FA incorrecto. Intento {attempts}/{MAX_2FA_ATTEMPTS}")

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
    # Rate limiting for refresh token endpoint
    from infrastructure.core.redis_rate_limiter import get_rate_limiter
    limiter = get_rate_limiter(requests=10, window=60)  # 10 requests per minute
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    if not limiter.is_allowed(client_ip):
        return jsonify({"message": "Too many refresh attempts. Please try again later."}), 429
    
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

# 2FA Management Endpoints
@bp.route('/api/auth/setup-2fa', methods=['POST'])
@jwt_required
def setup_2fa():
    """Setup 2FA for authenticated user - requires password verification"""
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    # P2.2 - Password verification required before setup
    password = data.get('password')
    if not password:
        return jsonify({"success": False, "message": "Password required for 2FA setup"}), 400
    
    # Verify user password
    user_data = MAuth.getUserById(current_user['user_id'])
    if not user_data or not check_password_hash(user_data.get('password', ''), password):
        SecureLogger.log_auth_attempt("2FA_SETUP_FAILED", user_data.get('email', 'unknown'), request.remote_addr)
        return jsonify({"success": False, "message": "Invalid password"}), 401
    
    # Generate new secret
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    qr_code = two_fa.generate_qr_code(user_data['email'], secret)
    
    # P1.4 - Encrypt secret before storing
    encryption_manager = get_encryption_manager()
    encrypted_secret = encryption_manager.encrypt(secret)
    
    # Store encrypted secret temporarily (not enabled yet)
    MAuth.updateUsuario(current_user['user_id'], {
        '2fa_secret': encrypted_secret,
        '2fa_enabled': False  # Will be enabled after verification
    })
    
    SecureLogger.log_auth_attempt("2FA_SETUP_INITIATED", user_data.get('email', 'unknown'), request.remote_addr)
    
    return jsonify({
        "success": True,
        "qr_code": qr_code,
        "secret": secret,  # Only show once for backup
        "message": "Scan QR code and verify with a code to enable 2FA"
    })

@bp.route('/api/auth/verify-2fa-setup', methods=['POST'])
@jwt_required
def verify_2fa_setup():
    """Verify 2FA setup and enable it"""
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    user_data = MAuth.getUserById(current_user['user_id'])
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Get and decrypt secret
    encryption_manager = get_encryption_manager()
    encrypted_secret = user_data.get('2fa_secret')
    if not encrypted_secret:
        return jsonify({"success": False, "message": "2FA not setup"}), 400
    
    try:
        secret = encryption_manager.decrypt(encrypted_secret)
    except Exception as e:
        SecureLogger.safe_log(f"Error decrypting 2FA secret: {str(e)}", "ERROR")
        return jsonify({"success": False, "message": "2FA setup error"}), 500
    
    # Verify the code
    two_fa = TwoFactorAuth()
    if not two_fa.verify_token(secret, data.get('code', '')):
        return jsonify({"success": False, "message": "Invalid verification code"}), 400
    
    # Enable 2FA
    MAuth.updateUsuario(current_user['user_id'], {'2fa_enabled': True})
    
    SecureLogger.log_auth_attempt("2FA_SETUP_COMPLETED", user_data.get('email', 'unknown'), request.remote_addr)
    
    return jsonify({
        "success": True,
        "message": "2FA enabled successfully"
    })

@bp.route('/api/auth/disable-2fa', methods=['POST'])
@jwt_required
def disable_2fa():
    """Disable 2FA - requires password verification"""
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    # P1.1 - Password verification required before disable
    password = data.get('password')
    if not password:
        return jsonify({"success": False, "message": "Password required to disable 2FA"}), 400
    
    # Verify user password
    user_data = MAuth.getUserById(current_user['user_id'])
    if not user_data or not check_password_hash(user_data.get('password', ''), password):
        SecureLogger.log_auth_attempt("2FA_DISABLE_FAILED", user_data.get('email', 'unknown'), request.remote_addr)
        return jsonify({"success": False, "message": "Invalid password"}), 401
    
    # Check if 2FA is enabled
    if not user_data.get('2fa_enabled', False):
        return jsonify({"success": False, "message": "2FA is not enabled"}), 400
    
    # Disable 2FA and remove secret
    MAuth.updateUsuario(current_user['user_id'], {
        '2fa_enabled': False,
        '2fa_secret': None
    })
    
    SecureLogger.log_auth_attempt("2FA_DISABLED", user_data.get('email', 'unknown'), request.remote_addr)
    
    return jsonify({
        "success": True,
        "message": "2FA disabled successfully"
    })

@bp.route('/api/auth/2fa-status', methods=['GET'])
@jwt_required
def get_2fa_status():
    """Get current 2FA status"""
    current_user = request.current_user
    user_data = MAuth.getUserById(current_user['user_id'])
    
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    return jsonify({
        "success": True,
        "2fa_enabled": user_data.get('2fa_enabled', False),
        "has_secret": bool(user_data.get('2fa_secret'))
    })
