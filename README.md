<div align="center">
  <img src="presentation/static/images/logo_sdb.png" alt="Logo Salesianos" width="120" />
  <h1>Agenda Salesiana SDB 🏛️</h1>
  <p><em>Sistema de Gestión Institucional Premium para la Inspectoría de las Antillas (República Dominicana)</em></p>

  [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![UI](https://img.shields.io/badge/UI-Premium_Glassmorphism-FF6B6B.svg?style=flat-square)]()
</div>

---

## 📖 Sobre el Proyecto

**AgendaSDB** es una plataforma web moderna y altamente optimizada para organizar, consultar y gestionar la intrincada red de Obras y Casas Salesianas. El sistema cuenta con una interfaz de usuario de diseño premium (inspirada en ecosistemas como Apple/Stripe), transiciones fluidas y soporte nativo y automático para **Modo Claro / Modo Oscuro**.

## ✨ Características Principales

- 🏢 **Gestión Inteligente de Casas y Obras**: Registro estructurado de casas (sedes) y sus respectivas obras (centros juveniles, parroquias, colegios), incluyendo metadata de contacto avanzado.
- 🔐 **Sistema de Roles y Accesos (RBAC)**:
  - `Superadmin`: Control absoluto del sistema, gestión de administradores y eliminación de registros.
  - `Admin`: Gestión de contenido, creación de obras y modificación de usuarios estándar.
  - `User`: Acceso de lectura y consulta de todo el directorio institucional.
- 📄 **Reportes Institucionales Automatizados**: Generación de reportes PDF de alta calidad utilizando `fpdf2`, con inyección dinámica de la identidad corporativa y membretes oficiales de SDB.
- 🎨 **Interfaz Premium & Dark Mode**:
  - Paneles de administración con efecto *Glassmorphism*.
  - Sistema de modales unificados sin costuras (seamless modals) y animaciones orgánicas (curvas Bézier).
  - Integración nativa adaptable de **Modo Oscuro**, garantizando accesibilidad y estética impecable en ambos temas.
- 🛡️ **Arquitectura Robusta**:
  - Middleware de protección de rutas y persistencia de sesión segura por base de datos.
  - Alertas dinámicas tipo *Toast* y *Status Modals* para la retroalimentación al usuario en tiempo real.

## 🚀 Tecnologías Core

* **Backend**: Python 3.10+, Flask, Flask-Session.
* **Base de Datos**: MongoDB (PyMongo), MongoDB Atlas.
* **Frontend**: Custom Design System (CSS3 Vanilla con CSS Variables), HTML5 Semántico, JavaScript Moderno.
* **Reportes**: fpdf2 (Generación de PDF vectorial).

## 🛠️ Instalación y Despliegue Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/juanhp324/AgendaSDB.git
   cd AgendaSDB
   ```

2. **Configurar Entorno Virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   # .venv\Scripts\activate   # En Windows
   ```

3. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables de Entorno**:
   Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura vital:
   ```env
   MONGODB_URI=tu_mongo_uri_str_connection
   DATABASE_NAME=AgendaSDB
   SECRET_KEY=clave_secreta_super_segura
   ```

5. **Lanzar el Servidor**:
   ```bash
   python app.py
   ```
   *El sistema estará disponible en `http://localhost:5000`*

## 📄 Licencia y Uso

Este software es de arquitectura **privada e institucional**. Diseñado y optimizado exclusivamente para el directorio eclesiástico y administrativo de los Salesianos de Don Bosco en las Antillas.

---
<div align="center">
  <em>Desarrollado con ❤️ para los Salesianos de las Antillas.</em>
</div>
