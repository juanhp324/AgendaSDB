import json
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from infrastructure.core.redis_rate_limiter import get_rate_limiter
from infrastructure.core.safety import SecureLogger

class SessionCache:
    """
    Sistema de cache de sesiones en Redis con TTL
    Permite persistencia de sesiones across deployments y mejor rendimiento
    """
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hora por defecto
    
    def _get_redis(self):
        """Obtener cliente Redis"""
        if not self.redis_client:
            try:
                limiter = get_rate_limiter()
                self.redis_client = limiter.redis_client
            except Exception as e:
                SecureLogger.safe_log(f"Error getting Redis client for session cache: {str(e)}", "ERROR")
                return None
        return self.redis_client
    
    def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Guardar datos de sesión en Redis con TTL
        
        Args:
            session_id: ID único de la sesión
            session_data: Datos de la sesión
            ttl: Time to live en segundos (opcional)
            
        Returns:
            bool: True si se guardó exitosamente
        """
        redis_client = self._get_redis()
        if not redis_client:
            return False
        
        try:
            # Serializar datos de sesión
            serialized_data = json.dumps(session_data, default=str)
            
            # Usar TTL proporcionado o default
            expiration = ttl or self.default_ttl
            
            # Guardar en Redis
            key = f"session:{session_id}"
            result = redis_client.setex(key, expiration, serialized_data)
            
            if result:
                SecureLogger.safe_log(f"Session cached: {session_id} (TTL: {expiration}s)")
            
            return bool(result)
            
        except Exception as e:
            SecureLogger.safe_log(f"Error caching session {session_id}: {str(e)}", "ERROR")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos de sesión desde Redis
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Dict con datos de sesión o None si no existe
        """
        redis_client = self._get_redis()
        if not redis_client:
            return None
        
        try:
            key = f"session:{session_id}"
            serialized_data = redis_client.get(key)
            
            if not serialized_data:
                return None
            
            # Deserializar datos
            session_data = json.loads(serialized_data)
            
            # Actualizar TTL para extender la sesión
            redis_client.expire(key, self.default_ttl)
            
            return session_data
            
        except Exception as e:
            SecureLogger.safe_log(f"Error getting session {session_id}: {str(e)}", "ERROR")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualizar datos específicos de una sesión
        
        Args:
            session_id: ID único de la sesión
            updates: Diccionario con datos a actualizar
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Actualizar datos
        session_data.update(updates)
        
        # Guardar con TTL extendido
        return self.set_session(session_id, session_data)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Eliminar sesión de Redis
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        redis_client = self._get_redis()
        if not redis_client:
            return False
        
        try:
            key = f"session:{session_id}"
            result = redis_client.delete(key)
            
            if result:
                SecureLogger.safe_log(f"Session deleted: {session_id}")
            
            return bool(result)
            
        except Exception as e:
            SecureLogger.safe_log(f"Error deleting session {session_id}: {str(e)}", "ERROR")
            return False
    
    def extend_session_ttl(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extender TTL de una sesión existente
        
        Args:
            session_id: ID único de la sesión
            ttl: Nuevo TTL en segundos (opcional)
            
        Returns:
            bool: True si se extendió exitosamente
        """
        redis_client = self._get_redis()
        if not redis_client:
            return False
        
        try:
            key = f"session:{session_id}"
            expiration = ttl or self.default_ttl
            
            result = redis_client.expire(key, expiration)
            
            if result:
                SecureLogger.safe_log(f"Session TTL extended: {session_id} (TTL: {expiration}s)")
            
            return bool(result)
            
        except Exception as e:
            SecureLogger.safe_log(f"Error extending session TTL {session_id}: {str(e)}", "ERROR")
            return False
    
    def get_user_sessions(self, user_id: str) -> list:
        """
        Obtener todas las sesiones activas de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List de session IDs
        """
        redis_client = self._get_redis()
        if not redis_client:
            return []
        
        try:
            # Buscar todas las claves de sesión
            pattern = "session:*"
            session_keys = redis_client.keys(pattern)
            
            user_sessions = []
            for key in session_keys:
                session_data = self.get_session(key.decode('utf-8').replace('session:', ''))
                if session_data and session_data.get('user_id') == user_id:
                    user_sessions.append(key.decode('utf-8'))
            
            return user_sessions
            
        except Exception as e:
            SecureLogger.safe_log(f"Error getting user sessions for {user_id}: {str(e)}", "ERROR")
            return []
    
    def revoke_user_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """
        Revocar todas las sesiones de un usuario (excepto una específica)
        
        Args:
            user_id: ID del usuario
            except_session: Session ID a no revocar (opcional)
            
        Returns:
            int: Número de sesiones revocadas
        """
        user_sessions = self.get_user_sessions(user_id)
        
        revoked_count = 0
        for session_key in user_sessions:
            session_id = session_key.replace('session:', '')
            
            # No revocar la sesión especificada
            if except_session and session_id == except_session:
                continue
            
            if self.delete_session(session_id):
                revoked_count += 1
        
        if revoked_count > 0:
            SecureLogger.safe_log(f"Revoked {revoked_count} sessions for user {user_id}")
        
        return revoked_count
    
    def cleanup_expired_sessions(self) -> int:
        """
        Limpiar sesiones expiradas (Redis lo hace automáticamente, pero podemos forzar limpieza)
        
        Returns:
            int: Número de sesiones limpiadas
        """
        redis_client = self._get_redis()
        if not redis_client:
            return 0
        
        try:
            # Redis maneja TTL automáticamente, pero podemos contar sesiones activas
            pattern = "session:*"
            session_keys = redis_client.keys(pattern)
            
            active_count = len(session_keys)
            SecureLogger.safe_log(f"Active sessions count: {active_count}")
            
            return active_count
            
        except Exception as e:
            SecureLogger.safe_log(f"Error counting sessions: {str(e)}", "ERROR")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de sesiones
        
        Returns:
            Dict con estadísticas
        """
        redis_client = self._get_redis()
        if not redis_client:
            return {}
        
        try:
            # Contar sesiones activas
            pattern = "session:*"
            session_keys = redis_client.keys(pattern)
            
            # Obtener memoria usada
            info = redis_client.info('memory')
            memory_used = info.get('used_memory_human', 'N/A')
            
            stats = {
                'active_sessions': len(session_keys),
                'memory_used': memory_used,
                'redis_connected': True
            }
            
            return stats
            
        except Exception as e:
            SecureLogger.safe_log(f"Error getting session stats: {str(e)}", "ERROR")
            return {'redis_connected': False, 'error': str(e)}

# Instancia global
session_cache = SessionCache()

def get_session_cache() -> SessionCache:
    """Obtener instancia global de SessionCache"""
    return session_cache
