import os
from datetime import timedelta
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='presentation/templates', static_folder='presentation/static')
app.secret_key = os.getenv('SECRET_KEY', 'agenda_secret_key_2024')
if app.secret_key == 'agenda_secret_key_2024':
    print("[WARNING] SECRET_KEY no definida en .env. Usando clave por defecto (Inseguro para producción).")
app.permanent_session_lifetime = timedelta(days=30)

# Importar blueprints
from application.routes.RAuth import bp as RAuth_bp
from application.routes.RInicio import bp as RInicio_bp

from application.routes.RCasas import bp as RCasas_bp
from application.routes.RUsuarios import bp as RUsuarios_bp

# Importar Pasarela de Aplicación (API Gateway)
from domain.VAuth import AppGateway

# Registrar blueprints
app.register_blueprint(RAuth_bp)
app.register_blueprint(RInicio_bp)
app.register_blueprint(RCasas_bp)
app.register_blueprint(RUsuarios_bp)

# Iniciar Pasarela de Aplicación
AppGateway(app)

# --- SEGURIDAD GLOBAL (Rate Limit & CSRF) ---
from infrastructure.core.safety import CSRFProtector, RateLimiter
from flask import abort

login_limiter = RateLimiter(requests=5, window=60)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=CSRFProtector.generate_token)

@app.before_request
def global_security_check():
    # 1. Rate Limiting (Siempre primero para registrar el intento incluso si falla el CSRF)
    if request.path == '/Login' and request.method == 'POST':
        if not login_limiter.is_allowed(request.remote_addr):
            return jsonify({
                "success": False, 
                "message": "Demasiadas peticiones. Por favor, espera un momento."
            }), 429

    # 2. CSRF Validation
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not token and request.is_json:
            token = request.get_json(silent=True).get('csrf_token')

        if not CSRFProtector.validate_token(token):
            abort(403, description="Token CSRF inválido o ausente.")

if __name__ == '__main__':
    app.run(debug=True)
