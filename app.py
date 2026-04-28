import os
from datetime import timedelta
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, template_folder='presentation/templates', static_folder='presentation/static')

    # --- Configuración ---
    if test_config:
        app.config.update(test_config)
    else:
        secret_key = os.getenv('SECRET_KEY')
        if not secret_key or secret_key == 'agenda_secret_key_2024':
            raise ValueError(
                "SECRET_KEY no configurada o usando valor por defecto inseguro. "
                "Por favor, establece una SECRET_KEY segura en tu archivo .env. "
                "Puedes generar una con: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        app.secret_key = secret_key

    app.permanent_session_lifetime = timedelta(days=30)

    # --- Infraestructura ---
    from infrastructure.monitoring.sentry_config import init_sentry
    init_sentry(app)

    from infrastructure.core.security_headers import init_security_headers
    init_security_headers(app)

    from infrastructure.core.jwt_auth import init_jwt_auth
    init_jwt_auth(app)

    # --- Blueprints ---
    from application.routes.RJWTAuth import bp as RJWTAuth_bp
    from application.routes.RInicio import bp as RInicio_bp
    from application.routes.RCasas import bp as RCasas_bp
    from application.routes.RUsuarios import bp as RUsuarios_bp
    from application.routes.RDerechos import bp as RDerechos_bp

    app.register_blueprint(RJWTAuth_bp)
    app.register_blueprint(RInicio_bp)
    app.register_blueprint(RCasas_bp)
    app.register_blueprint(RUsuarios_bp)
    app.register_blueprint(RDerechos_bp)

    # --- Pasarela de Aplicación (auth middleware) ---
    from domain.VAuth import AppGateway
    AppGateway(app)

    # --- Seguridad global (Rate Limit & CSRF) ---
    from infrastructure.core.safety import CSRFProtector
    from infrastructure.core.redis_rate_limiter import get_rate_limiter

    login_limiter = get_rate_limiter(requests=5, window=60)

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=CSRFProtector.generate_token)

    @app.before_request
    def global_security_check():
        if request.path == '/Login' and request.method == 'POST':
            if not login_limiter.is_allowed(request.remote_addr):
                return jsonify({
                    "success": False,
                    "message": "Demasiadas peticiones. Por favor, espera un momento."
                }), 429

        # CSRF no aplica en modo testing
        if app.config.get('TESTING'):
            return

        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not token and request.is_json:
                data = request.get_json(silent=True) or {}
                token = data.get('csrf_token')

            if not CSRFProtector.validate_token(token):
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"success": False, "message": "Token CSRF inválido o ausente."}), 403
                abort(403, description="Token CSRF inválido o ausente.")

    return app


# Instancia para gunicorn (app:app) y ejecución directa
app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
