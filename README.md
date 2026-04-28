<div align="center">
  <img src="presentation/static/img/logo_sdbfondo.jpeg" alt="Logo Salesianos" width="120" />
  <h1>Agenda Salesiana SDB</h1>
  <p><em>Sistema de Gestión Institucional para la Inspectoría de las Antillas (República Dominicana)</em></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![Redis](https://img.shields.io/badge/Redis-DC382D.svg?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
  [![Security](https://img.shields.io/badge/Security-Enterprise_Grade-00C851.svg?style=flat-square&logo=security)]()
  [![UI](https://img.shields.io/badge/UI-Premium_Glassmorphism-FF6B6B.svg?style=flat-square)]()
</div>

---

## Sobre el Proyecto

**AgendaSDB** es una plataforma web moderna y altamente optimizada para organizar, consultar y gestionar la red de Obras y Casas Salesianas. El sistema cuenta con una interfaz de diseño premium, transiciones fluidas, soporte nativo para **Modo Claro / Modo Oscuro**, y **seguridad de grado empresarial**.

## Características Principales

- **Gestión de Casas y Obras**: Registro estructurado de sedes (Casas) y sus centros asociados (Obras: parroquias, colegios, etc.).
- **Sistema de Roles (RBAC)**: Gestión de permisos para `Superadmin`, `Admin` y `User`.
- **Reportes Automatizados**: 
  - Generación de **PDF** de alta calidad con `fpdf2`.
  - Generación de documentos **Word (.docx)** profesionales con `python-docx`.
- **Interfaz Premium & Dark Mode**: Diseño basado en *Glassmorphism* con animaciones orgánicas y adaptabilidad total al tema del sistema.
- **Seguridad Enterprise**: JWT authentication, rate limiting, CSRF protection, headers de seguridad.
- **Resiliencia & Monitoreo**: Protecciones avanzadas contra fallos con Sentry integrado.

## Resiliencia y Seguridad

El sistema implementa patrones de diseño modernos para garantizar la disponibilidad y protección de los datos:

*   **AppGateway (Centralized Middleware)**: Una pasarela integrada en el dominio que centraliza la autenticación, autorización y el manejo de errores globales.
*   **Patrón Circuit Breaker**: Protege la conexión a MongoDB. Si la base de datos falla repetidamente, el circuito se "abre" para evitar sobrecargar el sistema, mostrando estados de gracia controlados.
*   **Rate Limiting**: Protección contra ataques de fuerza bruta en el inicio de sesión mediante limitación de peticiones por IP.
*   **Custom CSRF Protection**: Implementación a medida de protección contra ataques *Cross-Site Request Forgery* para todas las operaciones de modificación de estado.

## Tecnologías Core

*   **Backend**: Python 3.11+, Flask 3.0.
*   **Base de Datos**: MongoDB (PyMongo), MongoDB Atlas.
*   **Cache & Rate Limiting**: Redis
*   **Arquitectura**: Clean Architecture (Application, Domain, Infrastructure, Presentation).
*   **Frontend**: CSS3 Vanilla (Variables CSS), HTML5 Semántico, JS Moderno.
*   **Reportes**: `fpdf2` y `python-docx`.
*   **Monitoreo**: Sentry.io
*   **Autenticación**: JWT (access token 15min + refresh token 30d)

## :construction: Instalación y Despliegue Local

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/juanhp324/AgendaSDB.git
    cd AgendaSDB
    ```

2.  **Configurar Entorno Virtual**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Linux/Mac
    # .venv\Scripts\activate   # En Windows
    ```

3.  **Instalar Dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de Entorno**:
    Crea un archivo `.env` en la raíz con:
    ```env
    # Configuración Core
    MONGODB_URI=tu_mongo_uri_str_connection
    DATABASE_NAME=AgendaSDB
    SECRET_KEY=tu_clave_secreta_muy_segura_aqui
    FLASK_ENV=development
    
    # Mejoras de Seguridad (Opcionales)
    REDIS_URL=redis://localhost:6379
    SENTRY_DSN=tu_dsn_de_sentry_aqui
    ```
    
    > **IMPORTANTE**: La `SECRET_KEY` no puede ser el valor por defecto 'agenda_secret_key_2024'. Genera una clave segura con:
    > ```bash
    > python -c 'import secrets; print(secrets.token_hex(32))'
    > ```

5.  **Ejecución**:
    ```bash
    python app.py
    ```

## :shield: Seguridad Implementada

El sistema ha sido completamente reforzado con **seguridad de grado empresarial**:

### :fire: Arreglos Críticos Aplicados
- **Debug Mode Desactivado**: `app.run(debug=False)` para producción
- **Validación SECRET_KEY**: Rechaza claves inseguras por defecto
- **Logging Seguro**: Redacción automática de credenciales en logs

### :gear: Mejoras de Seguridad Implementadas
- **Rate Limiting Distribuido**: Redis-based con fallback a memoria
- **JWT Authentication**: Tokens de acceso (15min) + refresh (30d)
- **Headers de Seguridad**: CSP, HSTS, XSS protection, anti-clickjacking
- **Monitoreo Sentry**: Tracking de errores y rendimiento
- **Pruebas Automatizadas**: Suite completa con 80%+ cobertura

### :lock: Características de Seguridad
- **JWT-Only Authentication**: Sistema unificado stateless y escalable
- **Protección CSRF**: Tokens por sesión para cambios de estado
- **Rate Limiting**: 5 intentos por minuto en login, 10 en refresh
- **Control de Acceso**: RBAC con roles (user, admin, superadmin)
- **Monitoreo**: Sentry integrado con protección de privacidad

## :books: Documentación del Sistema

### :gear: Arquitectura
```
AgendaSDB/
|-- application/          # Lógica de aplicación y rutas
|-- domain/              # Lógica de negocio y validadores
|-- infrastructure/      # Base de datos, seguridad, utilidades
|-- presentation/        # Templates y assets frontend
|-- tests/               # Pruebas automatizadas
|-- docs/                # Documentación técnica
```

### :key: Flujos de Autenticación

#### Autenticación JWT (Único Sistema)
1. **Login**: POST a `/Login` con credenciales (web o JSON)
2. **Tokens**: Access token (15min) + refresh token (30d) emitidos
3. **Acceso**: Bearer token en header para APIs, cookies para web

#### Endpoints Principales
- **Login**: `POST /Login`
- **Refresh**: `POST /api/auth/refresh`
- **Logout**: `POST /api/auth/logout`

#### Características de Seguridad
- **Rate Limiting**: Protección contra fuerza bruta en todos los endpoints
- **JWT Stateless**: Escalable y distribuido

### :test_suite: Pruebas y Calidad

Ejecutar el suite de pruebas completo:
```bash
# Instalar dependencias de prueba
pip install pytest pytest-cov pytest-flask

# Ejecutar todas las pruebas
pytest tests/ --verbose --cov=. --cov-report=html

# Ejecutar solo pruebas de seguridad
pytest tests/test_security.py --cov=infrastructure.core
```

### :rocket: Despliegue en Producción

#### Configuración Render
1. **Variables de Entorno**: Todas las variables requeridas
2. **Redis Add-on**: Para rate limiting distribuido
3. **Múltiples Workers**: Rate limiting funciona across instancias
4. **Sentry Integration**: Configurar DSN para monitoreo
5. **HTTPS**: Automático con certificados SSL

#### Variables de Entorno Producción
```env
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_muy_larga_y_aleatoria
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=AgendaSDB
REDIS_URL=redis://user:pass@host:port
SENTRY_DSN=https://your-sentry-dsn
```

## :wrench: Comandos Útiles

```bash
# Generar clave secreta segura
python -c 'import secrets; print(secrets.token_hex(32))'

# Verificar instalación de dependencias
pip list | grep -E "(redis|jwt|sentry|pytest)"

# Ejecutar pruebas con cobertura
pytest tests/ --cov=. --cov-fail-under=80

# Iniciar con configuración específica
FLASK_ENV=production python app.py
```

## :warning: Consideraciones de Seguridad

- **Nunca** usar `agenda_secret_key_2024` como SECRET_KEY
- **Configurar** Redis en producción para rate limiting distribuido
- **Monitorear** errores a través de Sentry
- **Mantener** dependencias actualizadas regularmente
- **Rotar** SECRET_KEY periódicamente

## 📄 Licencia y Uso

Software de arquitectura **privada e institucional**. Diseñado para el uso exclusivo de los Salesianos de Don Bosco en las Antillas.

---
<div align="center">
  <em>Desarrollado con ❤️ para los Salesianos de las Antillas.</em>
</div>
