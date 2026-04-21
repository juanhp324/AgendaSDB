import time
import secrets
import logging
from functools import wraps
from flask import request, jsonify, session, abort

# Configure secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureLogger:
    """Secure logger that filters out sensitive information"""
    
    @staticmethod
    def safe_log(message, level='info'):
        """Log message without sensitive data"""
        safe_message = SecureLogger._sanitize_message(message)
        getattr(logger, level)(safe_message)
    
    @staticmethod
    def _sanitize_message(message):
        """Remove potential sensitive information from log messages"""
        import re
        # Remove potential passwords, tokens, keys
        sanitized = re.sub(r'(?i)(password|token|key|secret)[=:]\s*[^\s\}]+', r'\1=***REDACTED***', str(message))
        # Remove MongoDB connection strings
        sanitized = re.sub(r'mongodb\+?://[^\s\}]+', 'mongodb://***REDACTED***', sanitized)
        return sanitized

class RateLimiter:
    """
    Un limitador de tasa simple en memoria.
    Rastrea intentos por IP y tiempo.
    """
    def __init__(self, requests=5, window=60):
        self.requests = requests  # Máximo de peticiones
        self.window = window      # Ventana de tiempo en segundos
        self.hits = {}            # Diccionario para rastrear {ip: [timestamps]}

    def is_allowed(self, ip):
        now = time.time()
        # Limpiar registros antiguos fuera de la ventana
        if ip not in self.hits:
            self.hits[ip] = []
        
        self.hits[ip] = [t for t in self.hits[ip] if now - t < self.window]
        
        if len(self.hits[ip]) < self.requests:
            self.hits[ip].append(now)
            return True
        return False

def rate_limit(requests=5, window=60):
    """Decorador para aplicar rate limiting a una ruta de Flask."""
    limiter = RateLimiter(requests, window)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            if not limiter.is_allowed(ip):
                return jsonify({
                    "success": False, 
                    "message": "Demasiadas peticiones. Por favor, espera un momento."
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class CircuitBreaker:

    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            now = time.time()

            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    SecureLogger.safe_log(f"[CIRCUIT BREAKER] Intentando recuperación (HALF_OPEN) para {f.__name__}")
                else:
                    return self._fallback()

            try:
                result = f(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    SecureLogger.safe_log(f"[CIRCUIT BREAKER] Circuito CERRADO (Éxito en recuperación) para {f.__name__}")
                    self.failures = 0
                    self.state = "CLOSED"
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = now
                SecureLogger.safe_log(f"[CIRCUIT BREAKER] Fallo #{self.failures} en {f.__name__}: {str(e)}")
                
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    SecureLogger.safe_log(f"[CIRCUIT BREAKER] Circuito ABIERTO para {f.__name__}. Bloqueando llamadas.")
                
                raise e

        return wrapper

    def _fallback(self):
        raise ServiceUnavailableError("El servicio de base de datos no está disponible temporalmente.")

class ServiceUnavailableError(Exception):
    """Excepción para cuando el circuito está abierto."""
    pass

class CSRFProtector:
    """
    Protección básica contra CSRF hecha a medida.
    Genera un token único por sesión y lo valida en peticiones de cambio de estado.
    """
    @staticmethod
    def generate_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']

    @staticmethod
    def validate_token(token_to_check):
        stored_token = session.get('csrf_token')
        if not stored_token or not token_to_check or stored_token != token_to_check:
            return False
        return True
