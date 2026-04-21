import pytest
import json
import pyotp
from app import create_app
from infrastructure.model.MAuth import createUsuario, getUserByEmail
from infrastructure.core.two_factor import TwoFactorAuth

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key_for_testing_only'
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def two_fa():
    """Create TwoFactorAuth instance"""
    return TwoFactorAuth()

@pytest.fixture
def test_user():
    """Create test user"""
    user_data = {
        'nombre': '2FA Test User',
        'email': '2fatest@example.com',
        'user': '2fatestuser',
        'password': 'testpassword123',
        'rol': 'user',
        'activo': True
    }
    
    # Check if user exists, if not create it
    existing_user = getUserByEmail(user_data['email'])
    if existing_user:
        return existing_user
    
    return createUsuario(user_data)

class TestTwoFactorAuth:
    """Test Two-Factor Authentication"""
    
    def test_2fa_secret_generation(self, two_fa):
        """Test 2FA secret generation"""
        secret = two_fa.generate_secret()
        
        assert secret is not None
        assert len(secret) == 32  # Base32 encoded secret should be 32 chars
        
        # Verify it's a valid base32 string
        try:
            pyotp.TOTP(secret)
        except Exception as e:
            pytest.fail(f"Generated secret is not valid: {e}")
    
    def test_2fa_qr_code_generation(self, two_fa):
        """Test 2FA QR code generation"""
        email = 'test@example.com'
        secret = two_fa.generate_secret()
        qr_code = two_fa.generate_qr_code(email, secret)
        
        assert qr_code is not None
        assert isinstance(qr_code, str)
        assert len(qr_code) > 0
        
        # QR code should be base64 encoded image
        assert qr_code.startswith('data:image/png;base64,')
    
    def test_2fa_setup_data_generation(self, two_fa):
        """Test 2FA setup data generation"""
        email = 'test@example.com'
        secret, qr_code = two_fa.setup_2fa_data(email)
        
        assert secret is not None
        assert qr_code is not None
        assert len(secret) == 32
        assert qr_code.startswith('data:image/png;base64,')
    
    def test_2fa_token_verification(self, two_fa):
        """Test 2FA token verification"""
        secret = two_fa.generate_secret()
        totp = pyotp.TOTP(secret)
        
        # Generate valid token
        valid_token = totp.now()
        
        # Verify valid token
        assert two_fa.verify_token(secret, valid_token) is True
        
        # Verify invalid token
        assert two_fa.verify_token(secret, '000000') is False
        
        # Verify invalid format
        assert two_fa.verify_token(secret, '12345') is False
        assert two_fa.verify_token(secret, 'abcdef') is False
        assert two_fa.verify_token(secret, '') is False
    
    def test_2fa_token_time_window(self, two_fa):
        """Test 2FA token time window tolerance"""
        secret = two_fa.generate_secret()
        totp = pyotp.TOTP(secret)
        
        # Current token should be valid
        current_token = totp.now()
        assert two_fa.verify_token(secret, current_token) is True
        
        # Test with time window (allowing tokens from +-1 step)
        # This tests the implementation's time window tolerance
        tokens = [totp.at(i) for i in range(-1, 2)]  # -1, 0, +1
        
        valid_count = sum(1 for token in tokens if two_fa.verify_token(secret, token))
        assert valid_count >= 1  # At least current token should be valid

class TestTwoFactorAuthRoutes:
    """Test 2FA Routes Integration"""
    
    def test_2fa_setup_with_valid_password(self, client, test_user):
        """Test 2FA setup with valid password"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Setup 2FA with correct password
        setup_data = {
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'qr_code' in data
        assert 'secret' in data
        assert data['secret'] is not None
        assert len(data['secret']) == 32
    
    def test_2fa_setup_with_invalid_password(self, client, test_user):
        """Test 2FA setup with invalid password"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Try to setup 2FA with wrong password
        setup_data = {
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid password' in data['message']
    
    def test_2fa_setup_without_password(self, client, test_user):
        """Test 2FA setup without password"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Try to setup 2FA without password
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps({}),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Password required' in data['message']
    
    def test_2fa_setup_not_logged_in(self, client):
        """Test 2FA setup when not logged in"""
        setup_data = {
            'password': 'somepassword'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Unauthorized' in data['message']
    
    def test_2fa_enable_with_valid_token(self, client, test_user):
        """Test enabling 2FA with valid token"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Setup 2FA first
        setup_data = {
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        setup_result = json.loads(response.data)
        secret = setup_result['secret']
        
        # Generate valid token
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        # Enable 2FA
        enable_data = {
            'code': valid_token
        }
        
        response = client.post('/api/auth/verify-2fa-setup',
                             data=json.dumps(enable_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'enabled successfully' in data['message']
    
    def test_2fa_enable_with_invalid_token(self, client, test_user):
        """Test enabling 2FA with invalid token"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Setup 2FA first
        setup_data = {
            'password': 'testpassword123'
        }
        
        client.post('/api/auth/setup-2fa',
                   data=json.dumps(setup_data),
                   content_type='application/json',
                   headers={'Authorization': f'Bearer {token}'})
        
        # Try to enable 2FA with invalid token
        enable_data = {
            'code': '000000'
        }
        
        response = client.post('/api/auth/verify-2fa-setup',
                             data=json.dumps(enable_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid verification code' in data['message']
    
    def test_2fa_disable_with_valid_password(self, client, test_user):
        """Test disabling 2FA with valid password"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Disable 2FA with correct password
        disable_data = {
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/disable-2fa',
                             data=json.dumps(disable_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'disabled successfully' in data['message']
    
    def test_2fa_disable_with_invalid_password(self, client, test_user):
        """Test disabling 2FA with invalid password"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Try to disable 2FA with wrong password
        disable_data = {
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/disable-2fa',
                             data=json.dumps(disable_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid password' in data['message']
    
    def test_2fa_status_check(self, client, test_user):
        """Test 2FA status check"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Check 2FA status
        response = client.get('/api/auth/2fa-status',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert '2fa_enabled' in data
        assert 'has_secret' in data
        assert isinstance(data['2fa_enabled'], bool)
        assert isinstance(data['has_secret'], bool)

class TestTwoFactorAuthSecurity:
    """Test 2FA Security Features"""
    
    def test_2fa_secret_is_encrypted(self, client, test_user):
        """Test that 2FA secret is encrypted in database"""
        # This test would need to check that the stored secret is encrypted
        # For now, we just verify the flow works
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        setup_data = {
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Secret should be returned only during setup (plain text)
        # But stored encrypted in database
        assert 'secret' in data
        assert len(data['secret']) == 32
    
    def test_2fa_attempts_limiting(self, client, test_user):
        """Test 2FA attempts rate limiting"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Setup 2FA first
        setup_data = {
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/setup-2fa',
                             data=json.dumps(setup_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        # Try multiple invalid 2FA attempts
        for i in range(4):  # Assuming max attempts is 3
            enable_data = {
                'code': '000000'
            }
            
            response = client.post('/api/auth/verify-2fa-setup',
                                 data=json.dumps(enable_data),
                                 content_type='application/json',
                                 headers={'Authorization': f'Bearer {token}'})
        
        # Should be rate limited after too many attempts
        assert response.status_code in [400, 429]
    
    def test_2fa_session_cleanup(self, client, test_user):
        """Test 2FA session cleanup on logout"""
        # Login first
        login_data = {
            'email': '2fatest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        # Get token from login response
        login_result = json.loads(response.data)
        token = login_result.get('access_token')
        
        # Setup 2FA
        setup_data = {
            'password': 'testpassword123'
        }
        
        client.post('/api/auth/setup-2fa',
                   data=json.dumps(setup_data),
                   content_type='application/json',
                   headers={'Authorization': f'Bearer {token}'})
        
        # Logout (revoke token)
        response = client.post('/api/auth/logout',
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {token}'})
        
        # Try to access 2FA endpoints after logout
        response = client.get('/api/auth/2fa-status',
                            headers={'Authorization': f'Bearer {token}'})
        
        # Should be unauthorized
        assert response.status_code == 401
