#!/usr/bin/env python3
"""
Script para inicializar índices de MongoDB
Ejecutar este script para crear los índices necesarios en producción
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, OperationFailure

# Agregar el path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_indexes():
    """
    Crear índices necesarios para MongoDB
    """
    # Obtener configuración
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/?directConnection=true')
    database_name = os.getenv('DATABASE_NAME', 'AgendaSDB')
    
    print(f"Conectando a MongoDB: {database_name}")
    
    try:
        # Conectar a MongoDB
        client = MongoClient(mongodb_uri)
        db = client[database_name]
        
        # Verificar conexión
        client.admin.command('ping')
        print("Conexión exitosa a MongoDB")
        
        # Índices para la colección usuarios
        usuarios_collection = db.usuarios
        
        print("\nCreando índices para usuarios...")
        
        # Índice único en email (más importante)
        try:
            usuarios_collection.create_index(
                [("email", ASCENDING)], 
                unique=True, 
                name="idx_email_unique",
                background=True
            )
            print("  - Índice único en email: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice único en email: Ya existe")
            else:
                print(f"  - Índice único en email: Error - {e}")
        
        # Índice en user (nombre de usuario)
        try:
            usuarios_collection.create_index(
                [("user", ASCENDING)], 
                unique=True, 
                name="idx_user_unique",
                background=True
            )
            print("  - Índice único en user: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice único en user: Ya existe")
            else:
                print(f"  - Índice único en user: Error - {e}")
        
        # Índice en rol para consultas por rol
        try:
            usuarios_collection.create_index(
                [("rol", ASCENDING)], 
                name="idx_rol",
                background=True
            )
            print("  - Índice en rol: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice en rol: Ya existe")
            else:
                print(f"  - Índice en rol: Error - {e}")
        
        # Índice compuesto en activo y rol (para usuarios activos por rol)
        try:
            usuarios_collection.create_index(
                [("activo", ASCENDING), ("rol", ASCENDING)], 
                name="idx_activo_rol",
                background=True
            )
            print("  - Índice compuesto activo+rol: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice compuesto activo+rol: Ya existe")
            else:
                print(f"  - Índice compuesto activo+rol: Error - {e}")
        
        # Índice en 2fa_enabled para consultas de 2FA
        try:
            usuarios_collection.create_index(
                [("2fa_enabled", ASCENDING)], 
                name="idx_2fa_enabled",
                background=True
            )
            print("  - Índice en 2fa_enabled: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice en 2fa_enabled: Ya existe")
            else:
                print(f"  - Índice en 2fa_enabled: Error - {e}")
        
        # Índices para la colección casas
        casas_collection = db.casas
        
        print("\nCreando índices para casas...")
        
        # Índice en nombre para búsquedas
        try:
            casas_collection.create_index(
                [("nombre", ASCENDING)], 
                name="idx_nombre",
                background=True
            )
            print("  - Índice en nombre: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice en nombre: Ya existe")
            else:
                print(f"  - Índice en nombre: Error - {e}")
        
        # Índice en tipo para filtrar por tipo de institución
        try:
            casas_collection.create_index(
                [("tipo", ASCENDING)], 
                name="idx_tipo",
                background=True
            )
            print("  - Índice en tipo: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice en tipo: Ya existe")
            else:
                print(f"  - Índice en tipo: Error - {e}")
        
        # Índice en activo para casas activas
        try:
            casas_collection.create_index(
                [("activo", ASCENDING)], 
                name="idx_activo",
                background=True
            )
            print("  - Índice en activo: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice en activo: Ya existe")
            else:
                print(f"  - Índice en activo: Error - {e}")
        
        # Índice compuesto en ciudad y país para búsquedas geográficas
        try:
            casas_collection.create_index(
                [("ciudad", ASCENDING), ("pais", ASCENDING)], 
                name="idx_ciudad_pais",
                background=True
            )
            print("  - Índice compuesto ciudad+país: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice compuesto ciudad+país: Ya existe")
            else:
                print(f"  - Índice compuesto ciudad+país: Error - {e}")
        
        # Índice de texto para búsquedas full-text en nombre y ciudad
        try:
            casas_collection.create_index(
                [("nombre", "text"), ("ciudad", "text")], 
                name="idx_text_search",
                background=True
            )
            print("  - Índice de texto: OK")
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print("  - Índice de texto: Ya existe")
            else:
                print(f"  - Índice de texto: Error - {e}")
        
        # Mostrar resumen de índices creados
        print("\nResumen de índices:")
        
        print("\nÍndices en usuarios:")
        for index in usuarios_collection.list_indexes():
            print(f"  - {index['name']}: {index['key']}")
        
        print("\nÍndices en casas:")
        for index in casas_collection.list_indexes():
            print(f"  - {index['name']}: {index['key']}")
        
        # Estadísticas de la base de datos
        print(f"\nEstadísticas:")
        print(f"  - Usuarios: {usuarios_collection.count_documents({})}")
        print(f"  - Casas: {casas_collection.count_documents({})}")
        
        print("\n¡Índices creados exitosamente!")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()
    
    return True

def verify_indexes():
    """
    Verificar que los índices existen y están siendo utilizados
    """
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/?directConnection=true')
    database_name = os.getenv('DATABASE_NAME', 'AgendaSDB')
    
    try:
        client = MongoClient(mongodb_uri)
        db = client[database_name]
        
        print("Verificando índices...")
        
        # Verificar índice único en email
        usuarios = db.usuarios
        email_index = next((idx for idx in usuarios.list_indexes() if idx['name'] == 'idx_email_unique'), None)
        if email_index and email_index.get('unique'):
            print("  - Índice único en email: Verificado")
        else:
            print("  - Índice único en email: NO encontrado o no es único")
        
        # Verificar índice único en user
        user_index = next((idx for idx in usuarios.list_indexes() if idx['name'] == 'idx_user_unique'), None)
        if user_index and user_index.get('unique'):
            print("  - Índice único en user: Verificado")
        else:
            print("  - Índice único en user: NO encontrado o no es único")
        
        # Estadísticas de uso de índices
        print("\nEstadísticas de uso:")
        stats = db.command("collstats", "usuarios")
        if 'indexSizes' in stats:
            print("  - Tamaño de índices (usuarios):")
            for name, size in stats['indexSizes'].items():
                print(f"    - {name}: {size} bytes")
        
    except Exception as e:
        print(f"Error verificando índices: {e}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()
    
    return True

if __name__ == "__main__":
    print("=== Inicialización de Índices MongoDB ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print("Modo verificación")
        verify_indexes()
    else:
        print("Modo creación")
        create_indexes()
        print("\nPara verificar los índices creados, ejecuta:")
        print("python scripts/init_indexes.py verify")
