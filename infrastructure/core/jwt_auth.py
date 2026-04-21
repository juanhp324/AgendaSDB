import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from infrastructure.core.safety import SecureLogger

class JWTAuth:
    """
    JWT (JSON Web Token) authentication implementation
    """
    
    def __init__(self, app=None):
        self.app = app
        self.secret_key = None
        self.algorithm = 'HS256'
        self.token_expiration = datetime.timedelta(hours=24)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize JWT with Flask app"""
        self.secret_key = app.secret_key
        app.jwt_auth = self
        SecureLogger.safe_log("JWT authentication initialized")
    
    def generate_tokens(self, user_data):
        """
        Generate access and refresh tokens for user
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        now = datetime.datetime.utcnow()
        
        # Access token payload (short-lived)
        access_payload = {
            'user_id': str(user_data['_id']),
            'email': user_data['email'],
            'rol': user_data.get('rol', 'user'),
            'nombre': user_data.get('nombre', 'Usuario'),
            'iat': now,
            'exp': now + datetime.timedelta(minutes=15),  # 15 minutes expiration
            'type': 'access'
        }
        
        # Refresh token payload (long-lived)
        refresh_payload = {
            'user_id': str(user_data['_id']),
            'iat': now,
            'exp': now + datetime.timedelta(days=30),  # 30 days expiration
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        SecureLogger.safe_log(f"JWT tokens generated for user {user_data['email']}")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900  # 15 minutes in seconds
        }
    
    def verify_token(self, token, token_type='access'):
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            token_type: 'access' or 'refresh'
            
        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get('type') != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            SecureLogger.safe_log("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            SecureLogger.safe_log(f"Invalid JWT token: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New access token or None if invalid
        """
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        # Get user data to generate new tokens
        import infrastructure.model.MAuth as MAuth
        user = MAuth.getUserById(payload['user_id'])
        if not user:
            return None
        
        # Generate new access token
        now = datetime.datetime.utcnow()
        access_payload = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'rol': user.get('rol', 'user'),
            'nombre': user.get('nombre', 'Usuario'),
            'iat': now,
            'exp': now + datetime.timedelta(hours=1),
            'type': 'access'
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    def revoke_token(self, token):
        """
        Revoke a token (add to blacklist)
        For production, you'd want to store revoked tokens in Redis/database
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # In production, add token jti to blacklist
            SecureLogger.safe_log(f"Token revoked for user {payload.get('user_id')}")
            return True
        except jwt.InvalidTokenError:
            return False

# Decorators for protecting routes
def jwt_required(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Verify token
        jwt_auth = current_app.jwt_auth
        payload = jwt_auth.verify_token(token, 'access')
        if not payload:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*required_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401
            
            user_role = request.current_user.get('rol', 'user')
            if user_role not in required_roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# JWT token blacklist using Redis
import os
from infrastructure.core.redis_rate_limiter import get_rate_limiter

def is_token_blacklisted(token):
    """Check if token is blacklisted in Redis"""
    try:
        # Use Redis rate limiter connection for blacklist
        redis_client = get_rate_limiter().redis_client
        return redis_client.exists(f"blacklist:{token}")
    except Exception:
        # Fallback to memory if Redis fails
        return token in getattr(is_token_blacklisted, '_memory_fallback', set())

def blacklist_token(token):
    """Add token to Redis blacklist with TTL"""
    try:
        # Use Redis rate limiter connection for blacklist
        redis_client = get_rate_limiter().redis_client
        # Blacklist token for 24 hours (same as access token expiration)
        redis_client.setex(f"blacklist:{token}", 86400, "1")
    except Exception:
        # Fallback to memory if Redis fails
        if not hasattr(is_token_blacklisted, '_memory_fallback'):
            is_token_blacklisted._memory_fallback = set()
        is_token_blacklisted._memory_fallback.add(token)

# Initialize JWT auth instance
jwt_auth = JWTAuth()

def init_jwt_auth(app):
    """Initialize JWT authentication with Flask app"""
    jwt_auth.init_app(app)
    return jwt_auth
