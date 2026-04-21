from flask import Flask, request, jsonify
from infrastructure.core.safety import SecureLogger

class CSRFMiddleware:
    """
    CSRF Protection middleware for JSON/JWT endpoints
    """
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CSRF middleware with Flask app"""
        app.before_request(self._verify_csrf_for_json)
        SecureLogger.safe_log("CSRF middleware initialized for JSON endpoints")
    
    def _verify_csrf_for_json(self):
        """Verify CSRF token for JSON requests that modify state"""
        # Skip CSRF verification for safe methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return None
        
        # Skip CSRF verification for JWT endpoints (they use token-based auth)
        if request.path.startswith('/api/auth/'):
            return None
        
        # Skip CSRF verification for static files and health checks
        if (request.path.startswith('/static/') or 
            request.path.startswith('/favicon.ico') or
            request.path == '/health'):
            return None
        
        # For JSON requests, check if they have the CSRF header
        if request.is_json:
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                # Try to get from request body
                data = request.get_json(silent=True)
                if data:
                    csrf_token = data.get('csrf_token')
            
            if not csrf_token:
                SecureLogger.safe_log(f"CSRF token missing from {request.method} {request.path}")
                return jsonify({
                    'error': 'CSRF token required',
                    'message': 'CSRF protection: Include X-CSRF-Token header or csrf_token in request body'
                }), 403
            
            # Verify CSRF token (using session-based CSRF for now)
            # In a real implementation, you'd want to verify this against a stored token
            # For JWT endpoints, you might want to use a different approach
            
        return None

# Global instance
csrf_middleware = CSRFMiddleware()

def init_csrf_middleware(app: Flask):
    """Initialize CSRF middleware with Flask app"""
    csrf_middleware.init_app(app)
    return csrf_middleware
