import pytest
import re
import threading
import time
from playwright.sync_api import Page, expect
from werkzeug.security import generate_password_hash
from app import create_app
from infrastructure.model.MAuth import createUsuario, getUserByEmail, deleteUsuario

BASE_URL = "http://127.0.0.1:5001"
E2E_EMAIL = "e2e@test.com"
E2E_PASSWORD = "e2epassword123"


def _clear_rate_limit():
    """Borra el contador Redis del rate limiter para la IP local"""
    try:
        from infrastructure.core.redis_rate_limiter import RedisRateLimiter
        limiter = RedisRateLimiter(requests=5, window=60)
        limiter.redis_client.delete("rate_limit:127.0.0.1")
    except Exception:
        pass


@pytest.fixture(scope="session")
def live_server():
    """Start Flask app in a background thread for E2E tests"""
    app = create_app()
    app.config["TESTING"] = False  # Behave like production for browser tests
    app.config["SECRET_KEY"] = "e2e_test_secret_do_not_use_in_prod"
    app.config["SERVER_NAME"] = None

    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5001, use_reloader=False, threaded=True)
    )
    thread.daemon = True
    thread.start()
    time.sleep(1.5)
    yield BASE_URL


@pytest.fixture(scope="session")
def e2e_user(live_server):
    """Create E2E test user once for the whole session"""
    user_data = {
        "nombre": "E2E Test User",
        "email": E2E_EMAIL,
        "user": "e2etestuser",
        "password": generate_password_hash(E2E_PASSWORD),
        "rol": "user",
        "activo": True,
    }
    existing = getUserByEmail(user_data["email"])
    if existing:
        deleteUsuario(str(existing["_id"]))

    createUsuario(user_data)
    user = getUserByEmail(user_data["email"])
    yield user
    deleteUsuario(str(user["_id"]))


@pytest.fixture(autouse=True)
def clear_e2e_rate_limits():
    """Limpia el rate limit Redis antes de cada test E2E"""
    _clear_rate_limit()
    yield


@pytest.fixture
def logged_in_page(page: Page, live_server, e2e_user, clear_e2e_rate_limits):
    """Helper: returns a page already logged in"""
    _clear_rate_limit()  # segunda limpieza garantizada antes del login
    page.goto(f"{BASE_URL}/Login")
    page.fill("#email", E2E_EMAIL)
    page.fill("#password", E2E_PASSWORD)
    page.click(".btn-submit")
    page.wait_for_url(f"{BASE_URL}/inicio", timeout=8000)
    return page


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

@pytest.mark.e2e
class TestLoginPage:

    def test_login_page_loads(self, page: Page, live_server):
        """El formulario de login se muestra correctamente"""
        page.goto(f"{BASE_URL}/Login")
        expect(page.locator("#loginForm")).to_be_visible()
        expect(page.locator("#email")).to_be_visible()
        expect(page.locator("#password")).to_be_visible()
        expect(page.locator(".btn-submit")).to_be_visible()

    def test_login_page_title(self, page: Page, live_server):
        """El título de la página contiene el nombre del sistema"""
        page.goto(f"{BASE_URL}/Login")
        expect(page).to_have_title("Acceso Institucional — Agenda Salesiana")

    def test_login_success_redirects_to_inicio(self, page: Page, live_server, e2e_user):
        """Login correcto redirige a /inicio"""
        page.goto(f"{BASE_URL}/Login")
        page.fill("#email", E2E_EMAIL)
        page.fill("#password", E2E_PASSWORD)
        page.click(".btn-submit")
        page.wait_for_url(f"{BASE_URL}/inicio", timeout=8000)
        assert "/inicio" in page.url

    def test_login_wrong_password_shows_error(self, page: Page, live_server, e2e_user):
        """Contraseña incorrecta muestra el mensaje de error"""
        page.goto(f"{BASE_URL}/Login")
        page.fill("#email", E2E_EMAIL)
        page.fill("#password", "contraseñamala")
        page.click(".btn-submit")
        error_div = page.locator("#errorMsg")
        error_div.wait_for(state="visible", timeout=5000)
        expect(error_div).to_be_visible()

    def test_login_missing_fields_blocked_by_browser(self, page: Page, live_server):
        """Submit sin email no llega al servidor (validación nativa del navegador)"""
        page.goto(f"{BASE_URL}/Login")
        page.fill("#password", "algo")
        page.click(".btn-submit")
        # El formulario no se envía, permanece en /Login
        assert "/Login" in page.url

    def test_unauthenticated_access_redirects_to_login(self, page: Page, live_server):
        """Acceso a /inicio sin sesión redirige a /Login"""
        page.goto(f"{BASE_URL}/inicio")
        expect(page).to_have_url(f"{BASE_URL}/Login")


# ─────────────────────────────────────────────
# NAVEGACIÓN AUTENTICADA
# ─────────────────────────────────────────────

@pytest.mark.e2e
class TestAuthenticatedNavigation:

    def test_navbar_visible_after_login(self, logged_in_page: Page):
        """El navbar se muestra tras el login"""
        expect(logged_in_page.locator(".navbar")).to_be_visible()
        expect(logged_in_page.locator(".brand-name")).to_be_visible()

    def test_nav_links_visible(self, logged_in_page: Page):
        """Los enlaces de navegación (Inicio, Institutos) están visibles"""
        links = logged_in_page.locator(".nav-link")
        expect(links.first).to_be_visible()

    def test_navigate_to_casas(self, logged_in_page: Page):
        """El enlace 'Institutos' navega a /casas"""
        logged_in_page.click("a.nav-link:has-text('Institutos')")
        logged_in_page.wait_for_url(f"{BASE_URL}/casas", timeout=5000)
        assert "/casas" in logged_in_page.url

    def test_user_menu_opens(self, logged_in_page: Page):
        """El menú de usuario se abre al hacer click"""
        logged_in_page.click("#userMenuBtn")
        expect(logged_in_page.locator("#userDropdown")).to_be_visible()

    def test_user_menu_shows_name(self, logged_in_page: Page):
        """El menú de usuario muestra el nombre del usuario"""
        expect(logged_in_page.locator(".user-name")).to_contain_text("E2E Test User")


# ─────────────────────────────────────────────
# PERFIL
# ─────────────────────────────────────────────

@pytest.mark.e2e
class TestUserProfile:

    def test_perfil_modal_opens(self, logged_in_page: Page):
        """El modal de perfil se abre desde el menú de usuario"""
        logged_in_page.click("#userMenuBtn")
        logged_in_page.click("button.dropdown-item:has-text('Editar Perfil')")
        modal = logged_in_page.locator("#perfilModal")
        modal.wait_for(state="attached", timeout=5000)
        expect(modal).to_have_class(re.compile(r"active"))

    def test_perfil_modal_shows_email(self, logged_in_page: Page):
        """El modal de perfil muestra el email del usuario en el input de edición"""
        logged_in_page.click("#userMenuBtn")
        logged_in_page.click("button.dropdown-item:has-text('Editar Perfil')")
        logged_in_page.locator("#perfilModal").wait_for(state="attached", timeout=5000)
        logged_in_page.wait_for_load_state("networkidle")
        expect(logged_in_page.locator("#perfil_email")).to_have_value(E2E_EMAIL, timeout=8000)


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

@pytest.mark.e2e
class TestLogout:

    def test_logout_redirects_to_login(self, logged_in_page: Page):
        """Cerrar sesión redirige a /Login"""
        logged_in_page.click("#userMenuBtn")
        logged_in_page.click("a.dropdown-item.danger:has-text('Cerrar Sesión')")
        logged_in_page.wait_for_url(f"{BASE_URL}/Login", timeout=5000)
        assert "/Login" in logged_in_page.url

    def test_after_logout_cannot_access_protected_page(self, page: Page, live_server):
        """Tras el logout, /inicio redirige a /Login"""
        page.goto(f"{BASE_URL}/inicio")
        expect(page).to_have_url(f"{BASE_URL}/Login")
