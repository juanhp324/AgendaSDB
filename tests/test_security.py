import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.core.safety import RateLimiter, CSRFProtector, CircuitBreaker, SecureLogger
from infrastructure.core.redis_rate_limiter import RedisRateLimiter, FallbackRateLimiter, get_rate_limiter
from app import create_app

class TestSecurityFeatures(unittest.TestCase):
    """Test suite for security features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_ip = "192.168.1.1"
        self.sample_token = "test_csrf_token"
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key'})
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiter functionality"""
        limiter = RateLimiter(requests=3, window=60)
        
        # Should allow first 3 requests
        for i in range(3):
            self.assertTrue(limiter.is_allowed(self.sample_ip), 
                          f"Request {i+1} should be allowed")
        
        # 4th request should be blocked
        self.assertFalse(limiter.is_allowed(self.sample_ip), 
                        "4th request should be blocked")
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        with self.app.test_request_context():
            token = CSRFProtector.generate_token()
            self.assertIsNotNone(token)
            self.assertEqual(len(token), 64)  # 32 bytes * 2 (hex)
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation"""
        with self.app.test_request_context():
            from flask import session
            session['csrf_token'] = self.sample_token
            self.assertTrue(CSRFProtector.validate_token(self.sample_token))
            self.assertFalse(CSRFProtector.validate_token("invalid_token"))
            self.assertFalse(CSRFProtector.validate_token(""))
            self.assertFalse(CSRFProtector.validate_token(None))
    
    def test_secure_logger_sanitization(self):
        """Test that secure logging redacts sensitive information"""
        with patch('builtins.print') as mock_print:
            SecureLogger.safe_log("Login attempt with password=secret123")
            logged = mock_print.call_args[0][0]
            self.assertNotIn("secret123", logged)
            self.assertIn("REDACTED", logged)
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        # Should work normally in closed state
        @breaker
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(breaker.state, "CLOSED")
    
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=30)
        
        @breaker
        def failing_function():
            raise ValueError("Test error")
        
        # First failure
        with self.assertRaises(ValueError):
            failing_function()
        self.assertEqual(breaker.failures, 1)
        self.assertEqual(breaker.state, "CLOSED")
        
        # Second failure should open circuit
        with self.assertRaises(ValueError):
            failing_function()
        self.assertEqual(breaker.failures, 2)
        self.assertEqual(breaker.state, "OPEN")
    
    def test_fallback_rate_limiter(self):
        """Test fallback in-memory rate limiter"""
        limiter = FallbackRateLimiter(requests=2, window=60)
        
        # Should allow first 2 requests
        self.assertTrue(limiter.is_allowed(self.sample_ip))
        self.assertTrue(limiter.is_allowed(self.sample_ip))
        
        # 3rd request should be blocked
        self.assertFalse(limiter.is_allowed(self.sample_ip))
        
        # Test remaining requests
        remaining = limiter.get_remaining_requests(self.sample_ip)
        self.assertEqual(remaining, 0)
        
        # Reset and test again
        limiter.reset_limit(self.sample_ip)
        self.assertTrue(limiter.is_allowed(self.sample_ip))

class TestAppSecurity(unittest.TestCase):
    """Test application-level security"""
    
    def test_secret_key_validation(self):
        """Test that app rejects default secret key"""
        with patch.dict(os.environ, {'SECRET_KEY': 'agenda_secret_key_2024'}, clear=False):
            with self.assertRaises(ValueError) as context:
                create_app()  # No test_config so it reads SECRET_KEY from env
            self.assertIn("SECRET_KEY no configurada", str(context.exception))
    
    def test_debug_mode_disabled(self):
        """Test that debug mode is disabled in production"""
        # Check that app.run is called with debug=False
        # This would require mocking app.run in the actual test
        pass

if __name__ == '__main__':
    unittest.main()
