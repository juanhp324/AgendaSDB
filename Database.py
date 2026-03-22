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
MONGODB_URI = os.getenv("MONGODB_URI") or "mongodb://localhost:27017/"
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
        "nombre": "SDB Super Admin",
        "email": "superadmin@agenda.sdb.local",
        "password": generate_password_hash("super123"),
        "rol": "superadmin",
        "user": "sdb_super",
        "avatar": "",
        "activo": True
    },
    {
        "nombre": "Gestor Regional",
        "email": "gestor@agenda.sdb.local",
        "password": generate_password_hash("admin123"),
        "rol": "admin",
        "user": "gestor_01",
        "avatar": "",
        "activo": True
    },
    {
        "nombre": "Visitante Consulta",
        "email": "invitado@agenda.sdb.local",
        "password": generate_password_hash("user123"),
        "rol": "user",
        "user": "invitado",
        "avatar": "",
        "activo": True
    }
]

db.usuarios.insert_many(usuarios_seed)

# --- Casas y Obras ---
def generar_obras(ciudad_base, count=5):
    obras = []
    tipos = ["Centro Educativo", "Parroquia", "Obra Social", "Centro Juvenil", "Casa de Formación"]
    for i in range(count):
        tipo = tipos[i % len(tipos)]
        obras.append({
            "id": str(uuid.uuid4()),
            "nombre_obra": f"{tipo} - Sede {chr(65+i)}",
            "ciudad": ciudad_base,
            "telefono": f"+00 555-{1000 + i}",
            "direccion": f"Av. Principal, Edif. {i+1}, Sector {ciudad_base}",
            "correo": f"sede.{chr(97+i)}@{ciudad_base.lower().replace(' ', '.')}.sdb.local",
            "contacto": f"Hno. Encargado {i+1}",
            "telefono_contacto": f"+00 555-{5000 + i}"
        })
    return obras

casas_data = [
    ("Casa Inspectorial Central", "Ciudad Capital", "masculino", "Sede administrativa principal de la región."),
    ("Complejo Educativo Don Bosco", "Región Norte", "mixto", "Referente educativo con amplia trayectoria."),
    ("Centro de Formación San José", "Zona Industrial", "masculino", "Formación técnica y valores."),
    ("Misión Territorial Amazónica", "Selva Central", "mixto", "Presencia salesiana en territorios apartados."),
    ("Centro Juvenil y Oratorio", "Barrio Norte", "mixto", "Espacio de juego, oración y formación."),
    ("Casa Retiro Salesiano", "Zona Montañosa", "mixto", "Lugar de encuentro y espiritualidad."),
    ("Obra Social Mamá Margarita", "Sector Sur", "femenino", "Atención integral para la mujer y familia."),
    ("Instituto Tecnológico Bosco", "Ciudad Innovación", "masculino", "Vanguardia en educación técnica."),
    ("Parroquia y Centro Juvenil", "Pueblo Unido", "mixto", "Corazón espiritual de la comunidad."),
    ("Residencia Estudiantil Bosconia", "Ciudad Universitaria", "masculino", "Hogar para jóvenes estudiantes.")
]

casas_seed = []
for nombre, ciudad, tipo, historia in casas_data:
    casas_seed.append({
        "nombre": nombre,
        "historia": historia,
        "tipo": tipo,
        "obras": generar_obras(ciudad, 5),
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
