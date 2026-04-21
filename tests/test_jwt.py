import pytest
import json
import jwt
from app import create_app
from infrastructure.model.MAuth import createUsuario, getUserByEmail
from infrastructure.core.jwt_auth import JWTAuth

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
def jwt_auth(app):
    """Create JWT auth instance"""
    return JWTAuth()

@pytest.fixture
def test_user():
    """Create test user"""
    user_data = {
        'nombre': 'JWT Test User',
        'email': 'jwttest@example.com',
        'user': 'jwttestuser',
        'password': 'testpassword123',
        'rol': 'user',
        'activo': True
    }
    
    # Check if user exists, if not create it
    existing_user = getUserByEmail(user_data['email'])
    if existing_user:
        return existing_user
    
    return createUsuario(user_data)

class TestJWTAuth:
    """Test JWT Authentication"""
    
    def test_jwt_login_success(self, client, test_user):
        """Test successful JWT login"""
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'
        assert 'expires_in' in data
        assert data['expires_in'] == 900  # 15 minutes
    
    def test_jwt_login_invalid_credentials(self, client):
        """Test JWT login with invalid credentials"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_jwt_token_validation(self, app, jwt_auth, test_user):
        """Test JWT token validation"""
        # Generate tokens
        tokens = jwt_auth.generate_tokens(test_user)
        
        # Verify access token
        decoded = jwt_auth.verify_token(tokens['access_token'], 'access')
        assert decoded is not None
        assert decoded['user_id'] == str(test_user['_id'])
        assert decoded['email'] == test_user['email']
        assert decoded['type'] == 'access'
        
        # Verify refresh token
        decoded = jwt_auth.verify_token(tokens['refresh_token'], 'refresh')
        assert decoded is not None
        assert decoded['user_id'] == str(test_user['_id'])
        assert decoded['type'] == 'refresh'
    
    def test_jwt_token_refresh(self, client, test_user):
        """Test JWT token refresh"""
        # First login to get tokens
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        tokens = json.loads(response.data)
        
        # Refresh token
        refresh_data = {
            'refresh_token': tokens['refresh_token']
        }
        
        response = client.post('/api/auth/refresh',
                             data=json.dumps(refresh_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_jwt_protected_endpoint(self, client, test_user):
        """Test JWT protected endpoint"""
        # Login to get token
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        tokens = json.loads(response.data)
        
        # Access protected endpoint
        headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
    
    def test_jwt_protected_endpoint_without_token(self, client):
        """Test JWT protected endpoint without token"""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
    
    def test_jwt_protected_endpoint_invalid_token(self, client):
        """Test JWT protected endpoint with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid_token'
        }
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 401
    
    def test_jwt_logout(self, client, test_user):
        """Test JWT logout"""
        # Login to get token
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        tokens = json.loads(response.data)
        
        # Logout
        headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        response = client.post('/api/auth/logout', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_jwt_token_blacklist(self, client, test_user):
        """Test JWT token blacklisting"""
        # Login to get token
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        tokens = json.loads(response.data)
        
        # Logout to blacklist token
        headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        client.post('/api/auth/logout', headers=headers)
        
        # Try to use blacklisted token
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 401
    
    def test_jwt_role_based_access(self, client, test_user):
        """Test JWT role-based access control"""
        # Login to get token
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        tokens = json.loads(response.data)
        
        # Try to access admin endpoint as regular user
        headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        response = client.get('/api/auth/admin-only', headers=headers)
        
        assert response.status_code == 403
    
    def test_jwt_2fa_flow(self, client, test_user):
        """Test JWT 2FA flow"""
        # Login with user that has 2FA enabled (if setup)
        login_data = {
            'email': 'jwttest@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        data = json.loads(response.data)
        
        # If 2FA is enabled, should return temp token
        if 'requires_2fa' in data and data['requires_2fa']:
            assert 'temp_token' in data
            
            # Verify 2FA with temp token
            two_fa_data = {
                'temp_token': data['temp_token'],
                '2fa_token': '123456'  # This would need to be a valid TOTP token
            }
            
            response = client.post('/api/auth/verify-2fa',
                                 data=json.dumps(two_fa_data),
                                 content_type='application/json')
            
            # Should fail with invalid token, but endpoint should exist
            assert response.status_code in [401, 400]

class TestJWTSecurity:
    """Test JWT Security Features"""
    
    def test_jwt_token_expiration(self, app, jwt_auth, test_user):
        """Test JWT token expiration"""
        # Generate tokens
        tokens = jwt_auth.generate_tokens(test_user)
        
        # Verify valid token
        decoded = jwt_auth.verify_token(tokens['access_token'], 'access')
        assert decoded is not None
        
        # Try to verify expired token (this would require mocking time)
        # For now, just verify the structure is correct
        assert 'exp' in decoded
    
    def test_jwt_token_structure(self, app, jwt_auth, test_user):
        """Test JWT token structure"""
        # Generate tokens
        tokens = jwt_auth.generate_tokens(test_user)
        
        # Decode access token without verification
        decoded = jwt.decode(tokens['access_token'], options={'verify_signature': False})
        
        required_claims = ['user_id', 'email', 'rol', 'iat', 'exp', 'type']
        for claim in required_claims:
            assert claim in decoded
        
        assert decoded['type'] == 'access'
        assert decoded['email'] == test_user['email']
    
    def test_jwt_rate_limiting(self, client):
        """Test JWT endpoint rate limiting"""
        # Attempt multiple failed logins to trigger rate limiting
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        # Make multiple requests
        for i in range(6):  # Assuming rate limit is 5 per minute
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
        
        # The last request should be rate limited
        assert response.status_code == 429
    
    def test_jwt_refresh_rate_limiting(self, client):
        """Test JWT refresh endpoint rate limiting"""
        # Attempt multiple refresh requests without valid token
        refresh_data = {
            'refresh_token': 'invalid_token'
        }
        
        # Make multiple requests
        for i in range(11):  # Assuming rate limit is 10 per minute
            response = client.post('/api/auth/refresh',
                                 data=json.dumps(refresh_data),
                                 content_type='application/json')
        
        # The last request should be rate limited
        assert response.status_code == 429
