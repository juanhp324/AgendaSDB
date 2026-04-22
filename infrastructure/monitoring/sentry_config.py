import os
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from infrastructure.core.safety import SecureLogger

class SentryMonitor:
    """
    Sentry monitoring configuration for error tracking and performance monitoring
    """
    
    def __init__(self):
        self.enabled = False
        self.dsn = os.getenv('SENTRY_DSN')
        self.environment = os.getenv('FLASK_ENV', 'development')
        
    def init_app(self, app: Flask):
        """Initialize Sentry monitoring with Flask app"""
        if not self.dsn or self.dsn == 'your-sentry-dsn-here':
            SecureLogger.safe_log("Sentry DSN not configured, monitoring disabled")
            return
        
        try:
            sentry_sdk.init(
                dsn=self.dsn,
                integrations=[
                    FlaskIntegration(
                        transaction_style="url",
                        request_bodies="medium",
                        flask_version="3.0.0"
                    ),
                    RedisIntegration(),
                ],
                environment=self.environment,
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                profiles_sample_rate=0.1,  # 10% of transactions for profiling
                send_default_pii=False,  # Don't send personally identifiable information
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb,
                debug=app.debug,
            )
            
            self.enabled = True
            SecureLogger.safe_log(f"Sentry monitoring initialized for environment: {self.environment}")
            
            # Add custom tags and context
            self._set_context()
            
        except Exception as e:
            SecureLogger.safe_log(f"Failed to initialize Sentry: {str(e)}")
    
    def _before_send(self, event, hint):
        """Filter and modify events before sending to Sentry"""
        # Remove sensitive data from events
        if 'request' in event and 'data' in event['request']:
            event['request']['data'] = self._sanitize_data(event['request']['data'])
        
        # Filter out certain exceptions
        if 'exception' in event:
            exception_type = event['exception'].get('values', [{}])[0].get('type')
            if exception_type in ['HTTPException', 'NotFound']:
                return None  # Don't send 404s and other HTTP exceptions
        
        # Add custom context
        event['tags'] = {
            **event.get('tags', {}),
            'app_name': 'AgendaSDB',
            'version': '1.0.0'
        }
        
        return event
    
    def _before_breadcrumb(self, breadcrumb, hint):
        """Filter and modify breadcrumbs before sending"""
        # Remove sensitive data from breadcrumb data
        if 'data' in breadcrumb:
            breadcrumb['data'] = self._sanitize_data(breadcrumb['data'])
        
        return breadcrumb
    
    def _sanitize_data(self, data):
        """Remove sensitive information from data"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = ['password', 'token', 'secret', 'key', 'csrf_token', 'authorization']
        sanitized = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _set_context(self):
        """Set additional context for Sentry"""
        sentry_sdk.set_context("app", {
            "name": "AgendaSDB",
            "version": "1.0.0",
            "environment": self.environment
        })
        
        sentry_sdk.set_user({
            "id": "system",
            "ip_address": "{{auto}}",
            "username": "system"
        })
    
    def capture_exception(self, exception, extra=None):
        """Capture exception with additional context"""
        if not self.enabled:
            return
        
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_exception(exception)
    
    def capture_message(self, message, level='info'):
        """Capture a message"""
        if not self.enabled:
            return
        
        sentry_sdk.capture_message(message, level=level)
    
    def set_user_context(self, user_data):
        """Set user context for Sentry"""
        if not self.enabled:
            return
        
        sentry_sdk.set_user({
            "id": str(user_data.get('_id', 'anonymous')),
            "email": user_data.get('email', ''),
            "username": user_data.get('user', ''),
            "role": user_data.get('rol', 'user')
        })
    
    def add_breadcrumb(self, message, category='custom', level='info', data=None):
        """Add custom breadcrumb"""
        if not self.enabled:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )

# Global Sentry monitor instance
sentry_monitor = SentryMonitor()

def init_sentry(app: Flask):
    """Initialize Sentry monitoring with Flask app"""
    sentry_monitor.init_app(app)
    return sentry_monitor
