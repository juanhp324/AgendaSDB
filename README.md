# Agenda SDB 🏛️

Sistema de gestión para la Agenda Salesiana de la Inspectoría de las Antillas (República Dominicana). Una plataforma moderna y premium para organizar la información de las obras salesianas.

## ✨ Características

- **Gestión de Casas Salesianas**: Registro completo con dirección, historia y logos.
- **Sistema de Roles (RBAC)**:
  - `superadmin`: Control total del sistema.
  - `admin`: Gestión de obras y usuarios de nivel básico.
  - `user`: Consulta de información.
- **Reportes Institucionales**: Generación de PDFs profesionales con identidad salesiana.
- **Interfaz Premium**: Diseño basado en Glassmorphism, animaciones fluidas y paleta institucional SDB (Rojo/Azul).
- **Seguridad**: Persistencia de sesión, protección ante cambio de roles y autenticación robusta.

## 🚀 Tecnologías

- **Backend**: Python 3 + Flask
- **Base de Datos**: MongoDB (Atlas)
- **Frontend**: Vanilla JS, HTML5, CSS3 (Custom Design System)
- **Reportes**: fpdf2

## 🛠️ Instalación y Uso

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/juanhp324/AgendaSDB.git
   cd AgendaSDB
   ```

2. **Configurar el entorno**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Variables de Entorno**:
   Crea un archivo `.env` en la raíz con:
   ```env
   MONGODB_URI=tu_mongo_uri
   DATABASE_NAME=AgendaSDB
   SECRET_KEY=tu_secreto_aqui
   ```

4. **Ejecutar**:
   ```bash
   python app.py
   ```

## 📄 Licencia

Este proyecto es de uso institucional para la congregación salesiana.

---
*Desarrollado con ❤️ para los Salesianos de las Antillas.*
