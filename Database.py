"""
Script de inicialización de datos para AgendaSDB.
Ejecutar UNA sola vez para poblar la base de datos con
usuarios de prueba (uno por rol) y casas salesianas de muestra.

Uso:
    cd /home/juanhp324/Proyectos/AgendaSDB
    python Database.py
"""
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    MONGODB_URI = "mongodb://localhost:27017/"

cluster = MongoClient(MONGODB_URI)
db = cluster["AgendaSDB"]

# ── Limpiar colecciones ──
db.usuarios.delete_many({})
db.casas.delete_many({})

# ── Usuarios de prueba ──
db.usuarios.insert_many([
    {
        "nombre": "Super Administrador",
        "email": "super@salesiano.com",
        "user": "superadmin",
        "password": "super123",
        "rol": "superadmin",
        "avatar": ""
    },
    {
        "nombre": "Juan Admin",
        "email": "admin@salesiano.com",
        "user": "admin",
        "password": "admin123",
        "rol": "admin",
        "avatar": ""
    },
    {
        "nombre": "Maria Usuario",
        "email": "user@salesiano.com",
        "user": "maria",
        "password": "user123",
        "rol": "user",
        "avatar": ""
    },
])

# ── Casas Salesianas de muestra ──
db.casas.insert_many([
    {
        "nombre": "Casa Salesiana Don Bosco - Caracas",
        "telefono": "+58 212 461 1234",
        "direccion": "Av. Páez, El Paraíso, Caracas 1020",
        "web": "https://salesianos.ve",
        "correo": "caracas@salesiano.com",
        "ciudad": "Caracas",
        "historia": "Fundada en 1894, fue la primera presencia salesiana en Venezuela. Ha formado generaciones de jóvenes en el espíritu de Don Bosco.",
        "logo_filename": "",
        "contacto": "P. Carlos González",
        "telefono_contacto": "+58 414 121 0000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Instituto San Francisco de Sales - Valencia",
        "telefono": "+58 241 820 5678",
        "direccion": "Av. Bolívar Norte, Valencia, Carabobo",
        "web": "https://ifsvalencia.edu.ve",
        "correo": "valencia@salesiano.com",
        "ciudad": "Valencia",
        "historia": "Obra educativa con más de 60 años de historia, ofreciendo educación integral a jóvenes de la región centro-norte del país.",
        "logo_filename": "",
        "contacto": "P. Miguel Ángel Torres",
        "telefono_contacto": "+58 424 452 0000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Oratorio Salesiano San Juan Bosco - Maracaibo",
        "telefono": "+58 261 793 9012",
        "direccion": "Calle 72 con Av. 17, Maracaibo, Zulia",
        "web": "",
        "correo": "maracaibo@salesiano.com",
        "ciudad": "Maracaibo",
        "historia": "Casa de presencia salesiana en el Zulia dedicada a la atención de jóvenes en situación de riesgo mediante oratorio, talleres y deporte.",
        "logo_filename": "",
        "contacto": "P. José Ramírez",
        "telefono_contacto": "+58 426 621 0000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Centro Salesiano La Rinconada - Mérida",
        "telefono": "+58 274 263 3456",
        "direccion": "Prolongación Av. 2, El Llano, Mérida",
        "web": "https://salesianosmérida.com",
        "correo": "merida@salesiano.com",
        "ciudad": "Mérida",
        "historia": "Establecida en los años 60, la casa salesiana de Mérida integra educación formal, pastoral juvenil y trabajo comunitario en los Andes venezolanos.",
        "logo_filename": "",
        "contacto": "P. Antonio Vivas",
        "telefono_contacto": "+58 416 574 0000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Liceo Salesiano Padre Ojeda - Barquisimeto",
        "telefono": "+58 251 252 7890",
        "direccion": "Carrera 19 con Calle 36, Barquisimeto, Lara",
        "web": "",
        "correo": "barquisimeto@salesiano.com",
        "ciudad": "Barquisimeto",
        "historia": "Institución educativa salesiana que lleva el nombre del primer salesiano venezolano ordenado sacerdote, P. Cruz María Ojeda.",
        "logo_filename": "",
        "contacto": "P. Reinaldo Morales",
        "telefono_contacto": "+58 412 513 0000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
])

print("=" * 50)
print("✅ Base de datos inicializada correctamente")
print("=" * 50)
print("\nUsuarios de prueba:")
print("  superadmin@salesiano.com / super123  (superadmin)")
print("  admin@salesiano.com      / admin123  (admin)")
print("  user@salesiano.com       / user123   (user)")
print(f"\nCasas insertadas: {db.casas.count_documents({})}")
cluster.close()
