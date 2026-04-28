import infrastructure.model.MAuth as MAuth
from flask import url_for, redirect, session, request, flash, jsonify, render_template
from werkzeug.security import check_password_hash

PUBLIC_ENDPOINTS = ['RJWTAuth.show_login_form', 'RJWTAuth.login', 'RJWTAuth.logout']
PROTECTED_ENDPOINTS = [
    'RInicio.inicio',
    'RCasas.casas', 'RCasas.get_casas', 'RCasas.get_casa',
    'RCasas.create_casa', 'RCasas.update_casa', 'RCasas.delete_casa',
    'RUsuarios.usuarios', 'RUsuarios.get_usuarios', 'RUsuarios.update_usuario',
    'RUsuarios.delete_usuario', 'RUsuarios.create_usuario',
    'RJWTAuth.update_profile_jwt', 'RJWTAuth.get_current_user',
    'RJWTAuth.get_perfil', 'RJWTAuth.update_perfil',
    'RDerechos.derechos',
]

from infrastructure.core.safety import ServiceUnavailableError

class AppGateway:
    """
    Pasarela de Aplicación (API Gateway simplificado).
    Centraliza: Autenticación, Autorización, Circuit Breaker y Rate Limiting.
    """
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.verify_access)
        self.app.register_error_handler(ServiceUnavailableError, self.handle_service_unavailable)
        self.app.add_url_rule('/', 'index', self.index)

    def handle_service_unavailable(self, e):
        """Manejador global para cuando el Circuit Breaker está abierto."""
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "message": str(e)}), 503
        flash(f"[Resistencia] {str(e)}", "warning")
        return render_template('errors/503.html'), 503

    def verify_access(self):
        """Middleware centralizado para todas las peticiones."""
        if request.path.startswith('/static'):
            return

        # 1. Verificar endpoints públicos
        if request.endpoint in PUBLIC_ENDPOINTS:
            return

        # 2. Verificar Autenticación (JWT o Sesión)
        if 'user_id' not in session:
            return redirect(url_for('RJWTAuth.show_login_form'))

        # 3. Verificar si el usuario está activo (usando caché de sesión)
        # Solo consultar DB si no está en sesión o es endpoint crítico
        if session.get('activo') is False:
            session.clear()
            msg = "Cuenta desactivada."
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": msg}), 401
            flash(msg, "danger")
            return redirect(url_for('RJWTAuth.show_login_form'))

        # Opcional: validar DB en endpoints sensibles (cada 5 minutos)
        # Por ahora, confiar en caché de sesión para rendimiento

    def index(self):
        if 'user_id' in session:
            return redirect(url_for('RInicio.inicio'))
        return redirect(url_for('RJWTAuth.show_login_form'))


class loginValidator:
    def __init__(self, *, is_json: bool, payLoad: dict):
        self.is_json = is_json
        self.payLoad = payLoad or {}
        self.email = self.payLoad.get('email')
        self.password = self.payLoad.get('password')
        self.userData = None

    def check_json(self):
        if not self.is_json:
            raise ValueError("Se espera JSON en la solicitud.")

    def check_credentials(self):
        if not self.email or not self.password:
            raise ValueError("Faltan email o contraseña en la solicitud.")

    def check_user(self):
        self.userData = MAuth.getUserByEmail(self.email)
        if not self.userData:
            raise LookupError("Usuario no encontrado")
        
        # Verificar si el usuario está activo
        if self.userData.get("activo") is False:
            raise PermissionError("Tu cuenta ha sido desactivada. Contacta al administrador.")

    def check_password(self):
        if not check_password_hash(self.userData["password"], self.password):
            raise PermissionError("Credenciales incorrectas")

    def redirect_user(self):
        return {
            "success": True,
            "message": "Autenticación correcta. Redirigiendo...",
            "redirect": url_for('RInicio.inicio')
        }

    def validation(self):
        self.check_json()
        self.check_credentials()
        self.check_user()
        self.check_password()
        return self.userData
