import pytest
import json
from app import create_app
from infrastructure.model.MAuth import createUsuario, getUserByEmail
from werkzeug.security import generate_password_hash

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
def test_user():
    """Create test user"""
    user_data = {
        'nombre': 'Test User',
        'email': 'test@example.com',
        'user': 'testuser',
        'password': 'testpassword123',
        'rol': 'user',
        'activo': True
    }
    
    # Check if user exists, if not create it
    existing_user = getUserByEmail(user_data['email'])
    if existing_user:
        return existing_user
    
    return createUsuario(user_data)

class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login', 
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_info' in data
        assert data['user_info']['email'] == 'test@example.com'
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        login_data = {
            'email': 'test@example.com'
            # Missing password
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_logout(self, client, test_user):
        """Test logout functionality"""
        # First login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Then logout
        response = client.get('/Logout')
        
        assert response.status_code == 302  # Redirect
    
    def test_get_user_profile(self, client, test_user):
        """Test getting user profile"""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Get profile
        response = client.get('/get_user')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['email'] == 'test@example.com'
    
    def test_update_user_profile(self, client, test_user):
        """Test updating user profile"""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Update profile
        update_data = {
            'nombre': 'Updated Name',
            'avatar': 'new_avatar.jpg'
        }
        
        response = client.put('/update_perfil',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

class Test2FA:
    """Test Two-Factor Authentication"""
    
    def test_2fa_setup_requires_password(self, client, test_user):
        """Test that 2FA setup requires password"""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Try to setup 2FA without password
        response = client.post('/setup_2fa',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'contraseña' in data['message'].lower()
    
    def test_2fa_disable_requires_password(self, client, test_user):
        """Test that 2FA disable requires password"""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Try to disable 2FA without password
        response = client.post('/disable_2fa',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'contraseña' in data['message'].lower()
    
    def test_2fa_status(self, client, test_user):
        """Test getting 2FA status"""
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        client.post('/Login',
                   data=json.dumps(login_data),
                   content_type='application/json')
        
        # Get 2FA status
        response = client.get('/2fa_status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data
        assert 'configured' in data

class TestSecurity:
    """Test security features"""
    
    def test_rate_limiting(self, client):
        """Test rate limiting on login attempts"""
        # Attempt multiple failed logins to trigger rate limiting
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        # Make multiple requests
        for i in range(6):  # Assuming rate limit is 5 per minute
            response = client.post('/Login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
        
        # The last request should be rate limited
        assert response.status_code == 429
    
    def test_csrf_token_generation(self, client):
        """Test CSRF token generation"""
        response = client.get('/Login')
        
        # Should contain CSRF token in session or template
        assert response.status_code == 200
    
    def test_session_security(self, client, test_user):
        """Test session security"""
        # Login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/Login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        # Check that session contains user data
        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert 'email' in sess
            assert 'rol' in sess
