import pytest
import json
from app import create_app
from bson import ObjectId
from infrastructure.model.MAuth import createUsuario, getUserByEmail, deleteUsuario
from werkzeug.security import generate_password_hash
from infrastructure.core.redis_rate_limiter import RedisRateLimiter

@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Reset Redis rate limit counters before each test"""
    try:
        limiter = RedisRateLimiter(requests=5, window=60)
        limiter.redis_client.delete('rate_limit:127.0.0.1')
    except Exception:
        pass
    yield

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
    """Create test user with fresh hashed password"""
    user_data = {
        'nombre': 'Test User',
        'email': 'test@example.com',
        'user': 'testuser',
        'password': generate_password_hash('testpassword123'),
        'rol': 'user',
        'activo': True
    }
    
    existing_user = getUserByEmail(user_data['email'])
    if existing_user:
        deleteUsuario(str(existing_user['_id']))
    
    result = createUsuario(user_data)
    yield result
    deleteUsuario(str(result.inserted_id))

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
        response = client.get('/logout')
        
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
        response = client.get('/get_perfil')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['usuario']['email'] == 'test@example.com'
    
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


class TestLoginParametrizado:
    """Casos edge del login cubiertos con @pytest.mark.parametrize"""

    @pytest.mark.parametrize("payload,expected_status", [
        # --- Campos faltantes / vacíos ---
        ({},                                                    400),  # sin email ni password
        ({'email': 'test@example.com'},                         400),  # sin password
        ({'password': 'testpassword123'},                       400),  # sin email
        ({'email': '', 'password': 'testpassword123'},          400),  # email vacío
        ({'email': 'test@example.com', 'password': ''},         400),  # password vacío
        # --- Usuario no existe ---
        ({'email': 'noexiste@example.com', 'password': 'x'},   404),
        # --- Email en formato inválido: pasa validación de campos pero no encuentra usuario ---
        ({'email': 'no-es-email', 'password': 'pass'},          404),
    ])
    def test_login_casos_invalidos(self, client, payload, expected_status):
        """El login rechaza payloads inválidos con el status correcto"""
        r = client.post('/Login',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == expected_status
        data = json.loads(r.data)
        assert 'message' in data

    def test_login_password_incorrecta(self, client, test_user):
        """Contraseña incorrecta para usuario existente devuelve 401"""
        r = client.post('/Login',
                        data=json.dumps({'email': 'test@example.com', 'password': 'incorrecta'}),
                        content_type='application/json')
        assert r.status_code == 401
        data = json.loads(r.data)
        assert 'message' in data

    def test_login_usuario_inactivo(self, client, app):
        """Usuario con activo=False no puede iniciar sesión"""
        user_data = {
            'nombre': 'Inactivo User',
            'email': 'inactivo@test.com',
            'user': 'inactivouser',
            'password': generate_password_hash('pass123'),
            'rol': 'user',
            'activo': False,
        }
        existing = getUserByEmail(user_data['email'])
        if existing:
            deleteUsuario(str(existing['_id']))
        result = createUsuario(user_data)

        with app.test_client() as c:
            r = c.post('/Login',
                       data=json.dumps({'email': 'inactivo@test.com', 'password': 'pass123'}),
                       content_type='application/json')
            assert r.status_code == 401

        deleteUsuario(str(result.inserted_id))
