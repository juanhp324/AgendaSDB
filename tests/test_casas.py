import pytest
import json
from app import create_app
from infrastructure.model.MCasas import createCasa, deleteCasa
from infrastructure.model.MAuth import createUsuario, getUserByEmail, deleteUsuario
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key_for_testing_only'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _create_db_user(email, rol):
    data = {
        'nombre': f'Test {rol.capitalize()}',
        'email': email,
        'user': email.split('@')[0],
        'password': generate_password_hash('testpass123'),
        'rol': rol,
        'activo': True,
    }
    existing = getUserByEmail(email)
    if existing:
        deleteUsuario(str(existing['_id']))
    createUsuario(data)
    return getUserByEmail(email)


@pytest.fixture
def user_regular():
    user = _create_db_user('casastest_user@test.com', 'user')
    yield user
    deleteUsuario(str(user['_id']))


@pytest.fixture
def user_admin():
    user = _create_db_user('casastest_admin@test.com', 'admin')
    yield user
    deleteUsuario(str(user['_id']))


@pytest.fixture
def user_superadmin():
    user = _create_db_user('casastest_superadmin@test.com', 'superadmin')
    yield user
    deleteUsuario(str(user['_id']))


def _inject_session(client, user):
    """Inyecta sesión de usuario directamente en el test client (sin pasar por login)"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(user['_id'])
        sess['email'] = user['email']
        sess['nombre'] = user['nombre']
        sess['rol'] = user['rol']
        sess['activo'] = True


@pytest.fixture
def test_casa():
    """Crea una casa de prueba y la elimina al finalizar"""
    result = createCasa({
        'nombre': 'Instituto Salesiano Test',
        'tipo': 'masculino',
        'historia': 'Historia de prueba del instituto',
        'obras': [],
    })
    casa_id = str(result.inserted_id)
    yield casa_id
    try:
        deleteCasa(casa_id)
    except Exception:
        pass


# ─────────────────────────────────────────────
# ACCESO SIN AUTENTICACIÓN
# ─────────────────────────────────────────────

class TestAccesoSinAuth:

    def test_inicio_requiere_auth(self, client):
        """GET /inicio sin sesión redirige a /Login"""
        r = client.get('/inicio')
        assert r.status_code == 302
        assert '/Login' in r.headers['Location']

    def test_casas_page_requiere_auth(self, client):
        """GET /casas sin sesión redirige a /Login"""
        r = client.get('/casas')
        assert r.status_code == 302
        assert '/Login' in r.headers['Location']

    def test_get_casas_requiere_auth(self, client):
        """GET /get_casas sin sesión redirige a /Login"""
        r = client.get('/get_casas')
        assert r.status_code == 302

    def test_usuarios_requiere_auth(self, client):
        """GET /usuarios sin sesión redirige a /Login"""
        r = client.get('/usuarios')
        assert r.status_code == 302


# ─────────────────────────────────────────────
# CASAS — LECTURA (rol: user)
# ─────────────────────────────────────────────

class TestCasasLectura:

    def test_get_casas_retorna_lista(self, client, user_regular):
        """GET /get_casas con sesión devuelve JSON con lista"""
        _inject_session(client, user_regular)
        r = client.get('/get_casas')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True
        assert 'casas' in data
        assert isinstance(data['casas'], list)

    def test_get_casas_con_filtro_tipo(self, client, user_regular):
        """GET /get_casas?tipo=masculino filtra correctamente"""
        _inject_session(client, user_regular)
        r = client.get('/get_casas?tipo=masculino')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True
        for casa in data['casas']:
            assert casa.get('tipo', '').lower() == 'masculino'

    def test_get_casas_con_busqueda(self, client, user_regular, test_casa):
        """GET /get_casas?q=Salesiano devuelve resultados que coinciden"""
        _inject_session(client, user_regular)
        r = client.get('/get_casas?q=Salesiano')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True

    def test_get_casa_por_id(self, client, user_regular, test_casa):
        """GET /get_casa/<id> con ID válido devuelve la casa"""
        _inject_session(client, user_regular)
        r = client.get(f'/get_casa/{test_casa}')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True
        assert data['casa']['nombre'] == 'Instituto Salesiano Test'

    def test_get_casa_id_inexistente(self, client, user_regular):
        """GET /get_casa con ObjectId inexistente devuelve 404"""
        _inject_session(client, user_regular)
        r = client.get('/get_casa/000000000000000000000000')
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data['success'] is False


# ─────────────────────────────────────────────
# CASAS — PERMISOS (usuario 'user' no puede crear/editar/borrar)
# ─────────────────────────────────────────────

class TestCasasPermisos:

    def test_crear_casa_denegado_para_user(self, client, user_regular):
        """POST /create_casa con rol 'user' devuelve 403"""
        _inject_session(client, user_regular)
        r = client.post('/create_casa',
                        data=json.dumps({'nombre': 'Nueva Casa'}),
                        content_type='application/json')
        assert r.status_code == 403

    def test_eliminar_casa_denegado_para_user(self, client, user_regular, test_casa):
        """DELETE /delete_casa con rol 'user' devuelve 403"""
        _inject_session(client, user_regular)
        r = client.delete(f'/delete_casa/{test_casa}')
        assert r.status_code == 403

    def test_actualizar_casa_denegado_para_user(self, client, user_regular, test_casa):
        """PUT /update_casa con rol 'user' devuelve 403"""
        _inject_session(client, user_regular)
        r = client.put(f'/update_casa/{test_casa}',
                       data=json.dumps({'nombre': 'Actualizado'}),
                       content_type='application/json')
        assert r.status_code == 403


# ─────────────────────────────────────────────
# CASAS — CRUD (rol: admin/superadmin)
# ─────────────────────────────────────────────

class TestCasasCRUD:

    def test_crear_casa_exitoso(self, client, user_admin):
        """POST /create_casa con rol admin y datos válidos devuelve 201"""
        _inject_session(client, user_admin)
        payload = {'nombre': 'Casa Nueva', 'tipo': 'femenino', 'historia': '', 'obras': []}
        r = client.post('/create_casa',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['success'] is True
        # Limpieza
        deleteCasa(data['casa_id'])

    @pytest.mark.parametrize("payload,expected_status", [
        ({},                                        400),  # sin nombre
        ({'nombre': ''},                            400),  # nombre vacío
        ({'nombre': '   '},                         400),  # nombre solo espacios
        ({'nombre': 'OK', 'obras': 'no-es-lista'},  201),  # obras no es lista → se ignora y crea igual
    ])
    def test_crear_casa_validaciones(self, client, user_admin, payload, expected_status):
        """POST /create_casa con datos inválidos devuelve el status esperado"""
        _inject_session(client, user_admin)
        r = client.post('/create_casa',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == expected_status
        if expected_status == 201:
            data = json.loads(r.data)
            deleteCasa(data['casa_id'])

    def test_actualizar_casa_exitoso(self, client, user_admin, test_casa):
        """PUT /update_casa con datos válidos devuelve 200"""
        _inject_session(client, user_admin)
        r = client.put(f'/update_casa/{test_casa}',
                       data=json.dumps({'nombre': 'Instituto Actualizado', 'tipo': 'femenino'}),
                       content_type='application/json')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True

    def test_actualizar_casa_sin_datos(self, client, user_admin, test_casa):
        """PUT /update_casa sin campos válidos devuelve 400"""
        _inject_session(client, user_admin)
        r = client.put(f'/update_casa/{test_casa}',
                       data=json.dumps({'campo_invalido': 'valor'}),
                       content_type='application/json')
        assert r.status_code == 400

    def test_eliminar_casa_exitoso(self, client, user_superadmin):
        """DELETE /delete_casa con rol superadmin elimina la casa"""
        result = createCasa({'nombre': 'Para Eliminar', 'tipo': 'masculino', 'obras': []})
        casa_id = str(result.inserted_id)
        _inject_session(client, user_superadmin)
        r = client.delete(f'/delete_casa/{casa_id}')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True

    def test_eliminar_casa_inexistente(self, client, user_superadmin):
        """DELETE /delete_casa con ID inexistente devuelve 404"""
        _inject_session(client, user_superadmin)
        r = client.delete('/delete_casa/000000000000000000000000')
        assert r.status_code == 404


# ─────────────────────────────────────────────
# USUARIOS — ACCESO Y PERMISOS
# ─────────────────────────────────────────────

class TestUsuariosPermisos:

    def test_usuarios_page_denegada_a_user(self, client, user_regular):
        """GET /usuarios con rol 'user' devuelve 403"""
        _inject_session(client, user_regular)
        r = client.get('/usuarios')
        assert r.status_code == 403

    def test_usuarios_page_accesible_a_admin(self, client, user_admin):
        """GET /usuarios con rol 'admin' devuelve 200"""
        _inject_session(client, user_admin)
        r = client.get('/usuarios')
        assert r.status_code == 200

    def test_get_usuarios_denegado_a_user(self, client, user_regular):
        """GET /get_usuarios con rol 'user' devuelve 403"""
        _inject_session(client, user_regular)
        r = client.get('/get_usuarios')
        assert r.status_code == 403

    def test_get_usuarios_accesible_a_admin(self, client, user_admin):
        """GET /get_usuarios con rol 'admin' devuelve lista"""
        _inject_session(client, user_admin)
        r = client.get('/get_usuarios')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['success'] is True
        assert 'usuarios' in data

    @pytest.mark.parametrize("campo_faltante", [
        'nombre', 'email', 'user', 'password', 'rol'
    ])
    def test_create_usuario_campos_obligatorios(self, client, user_superadmin, campo_faltante):
        """POST /create_usuario sin campo obligatorio devuelve 400"""
        _inject_session(client, user_superadmin)
        payload = {
            'nombre': 'Nuevo Usuario',
            'email': 'nuevo@test.com',
            'user': 'nuevousuario',
            'password': 'pass123',
            'rol': 'user',
        }
        del payload[campo_faltante]
        r = client.post('/create_usuario',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data['success'] is False

    def test_create_usuario_exitoso(self, client, user_superadmin):
        """POST /create_usuario con datos completos crea el usuario"""
        _inject_session(client, user_superadmin)
        payload = {
            'nombre': 'Usuario Nuevo',
            'email': 'nuevo_temp@test.com',
            'user': 'nuevotemp',
            'password': 'pass123',
            'rol': 'user',
        }
        r = client.post('/create_usuario',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['success'] is True
        # Limpieza
        created = getUserByEmail('nuevo_temp@test.com')
        if created:
            deleteUsuario(str(created['_id']))
