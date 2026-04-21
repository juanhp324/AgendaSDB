import time
import secrets
import logging
from functools import wraps
from flask import request, jsonify, session, abort

# Configure secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureLogger:
    """
    Logger seguro que no expone información sensible e incluye contexto de usuario
    """
    
    @staticmethod
    def _get_user_context():
        """Obtener contexto del usuario actual"""
        try:
            from flask import session, request
            
            # Intentar obtener desde sesión
            user_id = session.get('user_id')
            email = session.get('email')
            
            # Intentar obtener desde JWT si está disponible
            if not user_id and hasattr(request, 'current_user'):
                user_id = request.current_user.get('user_id')
                email = request.current_user.get('email')
            
            # Intentar obtener desde IP si no hay usuario
            if not user_id:
                ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
                return f"IP:{ip}"
            
            user_info = f"user:{email}" if email else f"user_id:{user_id}"
            return user_info
        except Exception:
            return "anonymous"
    
    @staticmethod
    def safe_log(message: str, level: str = "INFO"):
        """Log seguro que redacta información sensible y agrega contexto de usuario"""
        # Redactar patrones comunes de información sensible
        sanitized_message = re.sub(r'password["\s]*[:=]["\s]*[^\s"]+', 'password=***REDACTED***', message, flags=re.IGNORECASE)
        sanitized_message = re.sub(r'secret["\s]*[:=]["\s]*[^\s"]+', 'secret=***REDACTED***', sanitized_message, flags=re.IGNORECASE)
        sanitized_message = re.sub(r'token["\s]*[:=]["\s]*[^\s"]+', 'token=***REDACTED***', sanitized_message, flags=re.IGNORECASE)
        sanitized_message = re.sub(r'key["\s]*[:=]["\s]*[^\s"]+', 'key=***REDACTED***', sanitized_message, flags=re.IGNORECASE)
        
        # Agregar contexto de usuario
        user_context = SecureLogger._get_user_context()
        
        # Log con timestamp y contexto
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [{user_context}] {sanitized_message}")
    
    @staticmethod
    def log_security_event(event: str, details: str = ""):
        """Log de eventos de seguridad con contexto"""
        SecureLogger.safe_log(f"SECURITY_EVENT: {event} - {details}", "WARNING")
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log de errores con contexto y usuario"""
        SecureLogger.safe_log(f"ERROR in {context}: {str(error)}", "ERROR")
    
    @staticmethod
    def log_auth_attempt(result: str, email: str = "", ip: str = ""):
        """Log de intentos de autenticación"""
        if email:
            SecureLogger.safe_log(f"AUTH_ATTEMPT: {result} for email: {email}", "INFO")
        elif ip:
            SecureLogger.safe_log(f"AUTH_ATTEMPT: {result} from IP: {ip}", "INFO")
        else:
            SecureLogger.safe_log(f"AUTH_ATTEMPT: {result}", "INFO")

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
