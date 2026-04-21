import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple
from infrastructure.core.safety import SecureLogger

class TwoFactorAuth:
    """
    Two-Factor Authentication implementation using TOTP (Time-based One-Time Password)
    """
    
    def __init__(self, app_name: str = "AgendaSDB"):
        self.app_name = app_name
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret key"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """
        Generate QR code for TOTP setup
        
        Args:
            user_email: User's email address
            secret: TOTP secret key
            
        Returns:
            Base64 encoded QR code image
        """
        try:
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_email,
                issuer_name=self.app_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_code_base64}"
            
        except Exception as e:
            SecureLogger.safe_log(f"Error generating QR code: {str(e)}")
            raise ValueError("Error generating QR code")
    
    def verify_token(self, secret: str, token: str) -> bool:
        """
        Verify TOTP token
        
        Args:
            secret: User's TOTP secret
            token: 6-digit token from authenticator app
            
        Returns:
            True if token is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 step tolerance
        except Exception as e:
            SecureLogger.safe_log(f"Error verifying TOTP token: {str(e)}")
            return False
    
    def get_current_token(self, secret: str) -> str:
        """Get current TOTP token for testing purposes"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.now()
        except Exception as e:
            SecureLogger.safe_log(f"Error generating TOTP token: {str(e)}")
            raise ValueError("Error generating token")
    
    def setup_2fa_data(self, user_email: str) -> Tuple[str, str]:
        """
        Generate complete 2FA setup data for a new user
        
        Returns:
            Tuple of (secret, qr_code_base64)
        """
        secret = self.generate_secret()
        qr_code = self.generate_qr_code(user_email, secret)
        return secret, qr_code

class TwoFactorSession:
    """
    Manage 2FA session state
    """
    
    @staticmethod
    def set_2fa_pending(session, user_id: str, user_data: dict):
        """Mark session as pending 2FA verification"""
        session['2fa_pending'] = True
        session['2fa_user_id'] = user_id
        session['2fa_user_data'] = user_data
        session['2fa_attempts'] = 0
        SecureLogger.safe_log(f"2FA verification pending for user {user_id}")
    
    @staticmethod
    def is_2fa_pending(session) -> bool:
        """Check if session is pending 2FA verification"""
        return session.get('2fa_pending', False)
    
    @staticmethod
    def get_pending_user_id(session) -> Optional[str]:
        """Get pending user ID from session"""
        return session.get('2fa_user_id')
    
    @staticmethod
    def get_pending_user_data(session) -> Optional[dict]:
        """Get pending user data from session"""
        return session.get('2fa_user_data')
    
    @staticmethod
    def increment_2fa_attempts(session):
        """Increment 2FA attempt counter using Redis"""
        try:
            from infrastructure.core.redis_rate_limiter import get_rate_limiter
            redis_client = get_rate_limiter().redis_client
            user_id = session.get('2fa_pending_user_id')
            
            if not user_id:
                return 1
            
            key = f"2fa_attempts:{user_id}"
            attempts = redis_client.incr(key)
            if attempts == 1:
                # Set expiration on first attempt (5 minutes)
                redis_client.expire(key, 300)
            
            return attempts
        except Exception:
            # Fallback to session if Redis fails
            attempts = session.get('2fa_attempts', 0) + 1
            session['2fa_attempts'] = attempts
            session['2fa_attempts_time'] = time.time()
            return attempts
    
    @staticmethod
    def clear_2fa_pending(session):
        """Clear 2FA pending state from session and Redis"""
        # Clear Redis attempts counter
        try:
            from infrastructure.core.redis_rate_limiter import get_rate_limiter
            redis_client = get_rate_limiter().redis_client
            user_id = session.get('2fa_pending_user_id')
            if user_id:
                redis_client.delete(f"2fa_attempts:{user_id}")
        except Exception:
            pass  # Ignore Redis errors
        
        # Clear session data
        session.pop('2fa_pending', None)
        session.pop('2fa_pending_user_id', None)
        session.pop('2fa_user_data', None)
        session.pop('2fa_attempts', None)
        session.pop('2fa_attempts_time', None)
    
    @staticmethod
    def complete_2fa_login(session, user_data: dict):
        """Complete 2FA login and set user session"""
        session.clear()  # Clear any existing session data
        session['user_id'] = str(user_data['_id'])
        session['email'] = user_data['email']
        session['rol'] = user_data.get('rol', 'user')
        session['nombre'] = user_data.get('nombre', 'Usuario')
        session['2fa_verified'] = True
        TwoFactorSession.clear_2fa_pending(session)
        SecureLogger.safe_log(f"2FA login completed for user {user_data['email']}")

# 2FA Configuration
MAX_2FA_ATTEMPTS = 3
TWO_FA_TIMEOUT = 300  # 5 minutes in seconds
