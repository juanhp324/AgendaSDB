"""
Script para poblar la base de datos AgendaSDB con datos de ejemplo.
Colecciones: usuarios, casas
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

MONGODB_URI = "mongodb://root:Servextex5252-@localhost:27017/?directConnection=true&readPreference=primary&replicaSet=rs0"
DATABASE_NAME = "AgendaSDB"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# ─── USUARIOS ──────────────────────────────────────────────────────────────
print("Poblando coleccion 'usuarios'...")
col_usuarios = db["usuarios"]
col_usuarios.delete_many({})

usuarios = [
    {
        "nombre": "Administrador Principal",
        "email": "admin@agendaSDB.com",
        "user": "admin",
        "password": generate_password_hash("Admin1234"),
        "rol": "superadmin",
        "activo": True,
        "created_at": datetime.utcnow()
    },
    {
        "nombre": "Juan Hernandez",
        "email": "juan@agendaSDB.com",
        "user": "juanh",
        "password": generate_password_hash("Juan1234"),
        "rol": "admin",
        "activo": True,
        "created_at": datetime.utcnow()
    },
    {
        "nombre": "Maria Gonzalez",
        "email": "maria@agendaSDB.com",
        "user": "mariag",
        "password": generate_password_hash("Maria1234"),
        "rol": "user",
        "activo": True,
        "created_at": datetime.utcnow()
    }
]
result = col_usuarios.insert_many(usuarios)
print(f"  OK {len(result.inserted_ids)} usuarios insertados")

# ─── CASAS ─────────────────────────────────────────────────────────────────
print("Poblando coleccion 'casas'...")
col_casas = db["casas"]
col_casas.delete_many({})

casas = [
    {
        "nombre": "Casa Salesiana Don Bosco - La Vega",
        "tipo": "masculino",
        "historia": "Fundada en 1958 por el P. Alberto Barral como primera mision salesiana en la region de La Vega. Durante decadas ha formado generaciones de jovenes a traves de la educacion tecnica y valores salesianos, siendo referente de la congregacion en la Republica Dominicana.",
        "obras": [
            {
                "id": "obra_001",
                "nombre_obra": "Colegio Don Bosco La Vega",
                "ciudad": "La Vega",
                "apartado_postal": "21000",
                "telefono": ["+1 809-573-2640", "+1 809-573-2641"],
                "direccion": "Av. Rivas Principales, La Vega, R.D.",
                "web": "https://donboscolavega.edu.do",
                "correo": ["info@donboscolavega.edu.do", "secretaria@donboscolavega.edu.do"],
                "contacto": "P. Carlos Mendez",
                "telefono_contacto": "+1 809-573-9999"
            },
            {
                "id": "obra_002",
                "nombre_obra": "Oratorio Festivo San Domenico Savio",
                "ciudad": "La Vega",
                "apartado_postal": "",
                "telefono": ["+1 809-573-3300"],
                "direccion": "Barrio Nuevo, La Vega, R.D.",
                "web": "",
                "correo": ["oratorio@donboscolavega.edu.do"],
                "contacto": "Hnos. Rafael Torres",
                "telefono_contacto": "+1 809-573-0110"
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Casa Salesiana San Juan Bosco - Santo Domingo",
        "tipo": "masculino",
        "historia": "Centro ubicado en la capital dominicana, establecido en 1965. Atiende a jovenes de sectores vulnerables con programas educativos, vocacionales y pastorales. Es el principal referente de la Inspectoria en la zona sur del pais.",
        "obras": [
            {
                "id": "obra_003",
                "nombre_obra": "Instituto Politecnico Salesiano",
                "ciudad": "Santo Domingo",
                "apartado_postal": "10100",
                "telefono": ["+1 809-682-1017", "+1 809-682-1018"],
                "direccion": "Calle Padre Billini #22, Ciudad Colonial, Santo Domingo",
                "web": "https://ipsalesiano.edu.do",
                "correo": ["admisiones@ipsalesiano.edu.do"],
                "contacto": "P. Manuel Rivas",
                "telefono_contacto": "+1 809-682-5050"
            },
            {
                "id": "obra_004",
                "nombre_obra": "Casa Juvenil Don Bosco",
                "ciudad": "Santo Domingo Este",
                "apartado_postal": "",
                "telefono": ["+1 809-591-4422"],
                "direccion": "Los Minas Sur, Santo Domingo Este",
                "web": "",
                "correo": ["casajuvenil@sdb.org.do", "juventud@sdb.org.do"],
                "contacto": "P. Luis Almonte",
                "telefono_contacto": "+1 809-591-7788"
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Casa Salesiana Maria Auxiliadora - Santiago",
        "tipo": "femenino",
        "historia": "Comunidad de Hijas de Maria Auxiliadora fundada en 1972 en la ciudad de Santiago. Trabaja principalmente en la educacion de la mujer y la familia, con enfasis en la formacion en valores y el desarrollo integral de la mujer dominicana.",
        "obras": [
            {
                "id": "obra_005",
                "nombre_obra": "Colegio Maria Auxiliadora",
                "ciudad": "Santiago de los Caballeros",
                "apartado_postal": "51000",
                "telefono": ["+1 809-575-3344", "+1 809-575-3345"],
                "direccion": "Av. Bartolome Colon, Reparto Amalia, Santiago",
                "web": "https://mariaauxiladorasantiago.edu.do",
                "correo": ["info@mariaauxiliadora.edu.do", "direccion@mariaauxiliadora.edu.do"],
                "contacto": "Hna. Rosa de la Cruz",
                "telefono_contacto": "+1 809-575-1001"
            },
            {
                "id": "obra_006",
                "nombre_obra": "Centro de Capacitacion Femenina",
                "ciudad": "Santiago de los Caballeros",
                "apartado_postal": "",
                "telefono": ["+1 809-575-6677"],
                "direccion": "Calle del Sol #88, Santiago",
                "web": "",
                "correo": ["capacitacion@fma.org.do"],
                "contacto": "Hna. Carmen Pena",
                "telefono_contacto": "+1 809-575-2200"
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Casa Salesiana San Francisco de Sales - Moca",
        "tipo": "masculino",
        "historia": "Presencia salesiana en Moca desde 1985, brindando educacion tecnica y pastoral a los jovenes de la Region Norte. Es reconocida por su fuerte vinculacion con las comunidades rurales del Cibao central.",
        "obras": [
            {
                "id": "obra_007",
                "nombre_obra": "Escuela Tecnica San Francisco",
                "ciudad": "Moca",
                "apartado_postal": "42000",
                "telefono": ["+1 809-578-4499"],
                "direccion": "Carretera Moca-La Vega Km 3, Moca",
                "web": "",
                "correo": ["tecnica@salesianosmoca.org"],
                "contacto": "P. Pedro Mateo",
                "telefono_contacto": "+1 809-578-0001"
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

result = col_casas.insert_many(casas)
print(f"  OK {len(result.inserted_ids)} casas insertadas")

client.close()
print("\n=== Base de datos poblada exitosamente ===")
print("\nCredenciales de acceso:")
print("  superadmin -> email: admin@agendaSDB.com  | pass: Admin1234")
print("  admin      -> email: juan@agendaSDB.com   | pass: Juan1234")
print("  user       -> email: maria@agendaSDB.com  | pass: Maria1234")
