import os
from datetime import timedelta
from flask import Flask, redirect, url_for, session, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='presentation/templates', static_folder='presentation/static')
app.secret_key = os.getenv('SECRET_KEY', 'agenda_secret_key_2024')
app.permanent_session_lifetime = timedelta(days=30)

# Importar blueprints
from application.routes.RAuth import bp as RAuth_bp
from application.routes.RInicio import bp as RInicio_bp

from application.routes.RCasas import bp as RCasas_bp
from application.routes.RUsuarios import bp as RUsuarios_bp

# Importar validador de autenticación
from domain.VAuth import authValidator

# Registrar blueprints
app.register_blueprint(RAuth_bp)
app.register_blueprint(RInicio_bp)
app.register_blueprint(RCasas_bp)
app.register_blueprint(RUsuarios_bp)

# Validaciones de autenticación
authValidator(app)

if __name__ == '__main__':
    app.run(debug=True)
