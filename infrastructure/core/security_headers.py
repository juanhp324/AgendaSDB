from flask import Flask, after_this_request
from infrastructure.core.safety import SecureLogger

class SecurityHeaders:
    """
    Security headers middleware similar to Helmet.js for Node.js
    """
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security headers middleware"""
        app.after_request(self._add_security_headers)
        SecureLogger.safe_log("Security headers middleware initialized")
    
    @staticmethod
    def _add_security_headers(response):
        """Add security headers to HTTP responses"""
        # Content Security Policy (CSP) - Different for dev/prod
        import os
        is_production = os.getenv('FLASK_ENV') == 'production'
        
        if is_production:
            # Production CSP - Strict, no unsafe-eval or unsafe-inline
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com",
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",
                "connect-src 'self'",
                "frame-ancestors 'none'",  # Prevent clickjacking
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests"  # Force HTTPS in production
            ]
        else:
            # Development CSP - More permissive for development
            csp_directives = [
                "default-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com",
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",
                "connect-src 'self' ws: wss: https://cdn.jsdelivr.net",  # Allow WebSocket for hot reload + source maps
                "frame-ancestors 'none'",  # Prevent clickjacking
                "base-uri 'self'",
                "form-action 'self'"
            ]
        
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # X-Frame-Options (legacy clickjacking protection)
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options (prevent MIME sniffing)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection (legacy XSS protection)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "autoplay=()",
            "encrypted-media=()",
            "fullscreen=()",
            "picture-in-picture=()",
        ]
        response.headers['Permissions-Policy'] = ', '.join(permissions_policy)
        
        # Strict-Transport-Security (HSTS) - only in production
        import os
        if os.getenv('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Additional security headers
        response.headers['X-DNS-Prefetch-Control'] = 'off'
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Remove server information
        response.headers['Server'] = 'AgendaSDB'
        response.headers.pop('X-Powered-By', None)
        
        return response

def init_security_headers(app: Flask):
    """Initialize security headers with Flask app"""
    SecurityHeaders(app)
    return SecurityHeaders
