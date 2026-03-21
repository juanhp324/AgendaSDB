import infrasture.model.MAuth as MAuth
from flask import url_for, redirect, session, request, flash, jsonify

PUBLIC_ENDPOINTS = ['RAuth.show_login_form', 'RAuth.Login', 'RAuth.logout']
PROTECTED_ENDPOINTS = [
    'RInicio.inicio',
    'RCasas.casas', 'RCasas.get_casas', 'RCasas.get_casa',
    'RCasas.create_casa', 'RCasas.update_casa', 'RCasas.delete_casa',
    'RUsuarios.usuarios', 'RUsuarios.get_usuarios', 'RUsuarios.update_usuario',
    'RUsuarios.delete_usuario', 'RUsuarios.create_usuario',
    'RAuth.update_perfil', 'RAuth.get_perfil',
]

class authValidator:
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.verify_authentication)
        self.app.add_url_rule('/', 'index', self.index)

    def verify_authentication(self):
        if request.path.startswith('/static'):
            return
        if request.endpoint in PUBLIC_ENDPOINTS:
            return
        if 'user_id' not in session:
            return redirect(url_for('RAuth.show_login_form'))
        
        user = MAuth.getUserById(session['user_id'])
        if not user:
            session.clear()
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": "Sesión inválida o cuenta eliminada. Inicia sesión de nuevo."}), 401
            flash("Tu sesión es inválida o tu cuenta fue eliminada. Por favor, inicia sesión de nuevo.", "danger")
            return redirect(url_for('RAuth.show_login_form'))

    def index(self):
        if 'user_id' in session:
            return redirect(url_for('RInicio.inicio'))
        return redirect(url_for('RAuth.show_login_form'))


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
        if self.password != self.userData["password"]:
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
