import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from infrastructure.core.safety import SecureLogger

class EncryptionManager:
    """
    Gestor de encriptación para secrets sensibles usando Fernet
    """
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Obtener o crear clave de encriptación"""
        # Intentar obtener desde variable de entorno
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            try:
                # Validar que es base64 válido de 32 bytes
                decoded = base64.urlsafe_b64decode(env_key.encode() + b'==')
                if len(decoded) >= 32:
                    return env_key.encode()  # Fernet espera la clave en base64, no bytes crudos
            except Exception as e:
                SecureLogger.safe_log(f"Error decoding ENCRYPTION_KEY: {str(e)}")
        
        # Generar nueva clave si no existe
        key = Fernet.generate_key()
        SecureLogger.safe_log("Generated new encryption key - save this ENCRYPTION_KEY for production:")
        SecureLogger.safe_log(key.decode())
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encriptar datos
        
        Args:
            data: Datos a encriptar
            
        Returns:
            Datos encriptados en base64
        """
        try:
            if not data:
                return ""
            
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            SecureLogger.safe_log(f"Error encrypting data: {str(e)}")
            raise ValueError("Error encriptando datos")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Desencriptar datos
        
        Args:
            encrypted_data: Datos encriptados en base64
            
        Returns:
            Datos desencriptados
        """
        try:
            if not encrypted_data:
                return ""
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            SecureLogger.safe_log(f"Error decrypting data: {str(e)}")
            raise ValueError("Error desencriptando datos")

# Instancia global del gestor de encriptación
encryption_manager = EncryptionManager()

def get_encryption_manager() -> EncryptionManager:
    """Obtener instancia del gestor de encriptación"""
    return encryption_manager
