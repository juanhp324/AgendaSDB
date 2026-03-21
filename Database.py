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
import uuid
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Configuración de MongoDB
MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb://root:Servextex5252-@localhost:27017/"
DATABASE_NAME = os.getenv("DATABASE_NAME") or "AgendaSDB"

cluster = MongoClient(MONGODB_URI)
db = cluster[DATABASE_NAME]

print("=" * 50)
print(f"Iniciando limpieza de la base de datos: {DATABASE_NAME}")
print("=" * 50)

# --- Limpieza de Base de Datos ---
db.usuarios.delete_many({})
db.casas.delete_many({})

# --- Usuarios ---
usuarios_seed = [
    {
        "nombre": "Super Administrador",
        "email": "super@salesiano.com",
        "password": "super123",
        "rol": "superadmin",
        "user": "superadmin",
        "avatar": ""
    },
    {
        "nombre": "Administrador Local",
        "email": "admin@salesiano.com",
        "password": "admin123",
        "rol": "admin",
        "user": "admin",
        "avatar": ""
    },
    {
        "nombre": "Usuario Consulta",
        "email": "user@salesiano.com",
        "password": "user123",
        "rol": "user",
        "user": "user",
        "avatar": ""
    }
]

db.usuarios.insert_many(usuarios_seed)

# --- Casas y Obras ---
def generar_obras(ciudad_base, count=8):
    obras = []
    tipos = ["Colegio", "Oratorio", "Centro Juvenil", "Parroquia", "Escuela Técnica", "Casa de Retiro", "Misión", "Residencia"]
    for i in range(count):
        tipo = tipos[i % len(tipos)]
        obras.append({
            "id": str(uuid.uuid4()),
            "nombre_obra": f"{tipo} {i+1}",
            "ciudad": ciudad_base,
            "telefono": f"+58 2{i}2 {1000 + i}",
            "direccion": f"Calle {i+1}, Sector {ciudad_base}",
            "correo": f"obra{i+1}@salesiano.org",
            "contacto": f"Hno. Juan {i+1}",
            "telefono_contacto": f"+58 414 {5000 + i}"
        })
    return obras

casas_data = [
    ("Casa Salesiana Don Bosco", "Caracas", "masculino", "Casa matriz en la capital."),
    ("Instituto Salesiano San José", "Valencia", "masculino", "Referente en educación técnica."),
    ("Oratorio San Juan Bosco", "Maracaibo", "masculino", "Atención a la juventud zuliana."),
    ("Colegio María Auxiliadora", "San Cristóbal", "femenino", "Tradición femenina en los Andes."),
    ("Misión Salesiana Amazonas", "Puerto Ayacucho", "masculino", "Compromiso con pueblos indígenas."),
    ("UE Sor Eusebia Palomino", "Barquisimeto", "femenino", "Formación integral mariana."),
    ("Centro Juvenil La Vega", "Caracas", "masculino", "Deporte y valores."),
    ("Colegio Madre Mazzarello", "Coro", "femenino", "Presencia en el occidente."),
    ("Instituto San Javier", "Mérida", "masculino", "Excelencia académica."),
    ("Casa Laura Vicuña", "Los Teques", "femenino", "Espiritualidad juvenil."),
    ("Parroquia María Auxiliadora", "Boleíta", "masculino", "Centro espiritual."),
    ("Unidad Educativa Santa Marta", "Maracay", "femenino", "Educación básica de calidad."),
    ("Oratorio San Miguel", "Cumaná", "masculino", "Arte y comunidad."),
    ("Colegio Inmaculada", "Barcelona", "femenino", "Centenario de servicio."),
    ("Residencia San Felipe Neri", "Caracas", "masculino", "Hogar para estudiantes.")
]

casas_seed = []
for nombre, ciudad, tipo, historia in casas_data:
    casas_seed.append({
        "nombre": nombre,
        "historia": historia,
        "tipo": tipo,
        "obras": generar_obras(ciudad, 8),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

db.casas.insert_many(casas_seed)

print("-" * 50)
print("✅ Base de datos inicializada correctamente")
print(f"   - Usuarios: {db.usuarios.count_documents({})}")
print(f"   - Casas: {db.casas.count_documents({})}")
print(f"   - Obras por casa: 8")
print("-" * 50)
cluster.close()
