<div align="center">
  <img src="presentation/static/img/logo_sdbfondo.jpeg" alt="Logo Salesianos" width="120" />
  <h1>Agenda Salesiana SDB 🏛️</h1>
  <p><em>Sistema de Gestión Institucional para la Inspectoría de las Antillas (República Dominicana)</em></p>

  [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![UI](https://img.shields.io/badge/UI-Premium_Glassmorphism-FF6B6B.svg?style=flat-square)]()
</div>

---

## 📖 Sobre el Proyecto

**AgendaSDB** es una plataforma web moderna y altamente optimizada para organizar, consultar y gestionar la red de Obras y Casas Salesianas. El sistema cuenta con una interfaz de diseño premium, transiciones fluidas y soporte nativo para **Modo Claro / Modo Oscuro**.

## ✨ Características Principales

- 🏢 **Gestión de Casas y Obras**: Registro estructurado de sedes (Casas) y sus centros asociados (Obras: parroquias, colegios, etc.).
- 🔐 **Sistema de Roles (RBAC)**: Gestión de permisos para `Superadmin`, `Admin` y `User`.
- 📄 **Reportes Automatizados**: 
  - Generación de **PDF** de alta calidad con `fpdf2`.
  - Generación de documentos **Word (.docx)** profesionales con `python-docx`.
- 🎨 **Interfaz Premium & Dark Mode**: Diseño basado en *Glassmorphism* con animaciones orgánicas y adaptabilidad total al tema del sistema.
- 🛡️ **Resiliencia & Seguridad**: Protecciones avanzadas contra fallos y ataques (ver sección de Resiliencia).

## 🛡️ Resiliencia y Seguridad

El sistema implementa patrones de diseño modernos para garantizar la disponibilidad y protección de los datos:

*   **AppGateway (Centralized Middleware)**: Una pasarela integrada en el dominio que centraliza la autenticación, autorización y el manejo de errores globales.
*   **Patrón Circuit Breaker**: Protege la conexión a MongoDB. Si la base de datos falla repetidamente, el circuito se "abre" para evitar sobrecargar el sistema, mostrando estados de gracia controlados.
*   **Rate Limiting**: Protección contra ataques de fuerza bruta en el inicio de sesión mediante limitación de peticiones por IP.
*   **Custom CSRF Protection**: Implementación a medida de protección contra ataques *Cross-Site Request Forgery* para todas las operaciones de modificación de estado.

## 🛠️ Tecnologías Core

*   **Backend**: Python 3.10+, Flask 3.0.
*   **Base de Datos**: MongoDB (PyMongo), MongoDB Atlas.
*   **Arquitectura**: Clean Architecture (Application, Domain, Infrastructure, Presentation).
*   **Frontend**: CSS3 Vanilla (Variables CSS), HTML5 Semántico, JS Moderno.
*   **Reportes**: `fpdf2` y `python-docx`.

## 🚀 Instalación y Despliegue Local

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
    MONGODB_URI=tu_mongo_uri_str_connection
    DATABASE_NAME=AgendaSDB
    SECRET_KEY=clave_secreta_pro
    ```

5.  **Ejecución**:
    ```bash
    python app.py
    ```

## 📄 Licencia y Uso

Software de arquitectura **privada e institucional**. Diseñado para el uso exclusivo de los Salesianos de Don Bosco en las Antillas.

---
<div align="center">
  <em>Desarrollado con ❤️ para los Salesianos de las Antillas.</em>
</div>
