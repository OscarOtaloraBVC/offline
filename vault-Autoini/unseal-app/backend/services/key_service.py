import logging
from typing import List, Optional, Dict
import base64

from core.crypto import SecureKeyStore, KeyEncryption
from models.key_models import KeyCreate, KeyUpdate, KeyDelete

logger = logging.getLogger(__name__)

class KeyService:
    """Servicio para gestión de llaves de unseal"""
    
    def __init__(self):
        self.keystore = SecureKeyStore()
    
    def get_keys(self, password: str) -> List[str]:
        """
        Obtiene todas las llaves descifradas
        Args:
            password: Contraseña del admin para descifrar
        Returns:
            List[str]: Lista de llaves en texto plano
        Raises:
            ValueError: Si la contraseña es incorrecta
        """
        try:
            keys = self.keystore.get_keys(password)
            logger.info(f"Obtenidas {len(keys)} llaves")
            return keys
        except Exception as e:
            logger.error(f"Error obteniendo llaves: {e}")
            raise ValueError("No se pudieron obtener las llaves. Verifica la contraseña.")
    
    def add_key(self, key_data: KeyCreate) -> Dict:
        """
        Añade una nueva llave
        Args:
            key_data: Datos de la llave a añadir
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Obtener llaves existentes
            existing_keys = self.keystore.get_keys(key_data.password)
            
            # Verificar duplicados
            if key_data.key in existing_keys:
                raise ValueError("La llave ya existe en el almacén")
            
            # Añadir nueva llave
            existing_keys.append(key_data.key)
            self.keystore.save_keys(existing_keys, key_data.password)
            
            logger.info(f"Llave añadida. Total: {len(existing_keys)}")
            return {
                "success": True,
                "message": "Llave añadida correctamente",
                "total": len(existing_keys),
                "key_index": len(existing_keys)
            }
        except Exception as e:
            logger.error(f"Error añadiendo llave: {e}")
            raise
    
    def update_key(self, key_index: int, key_data: KeyUpdate) -> Dict:
        """
        Actualiza una llave existente
        Args:
            key_index: Índice de la llave (1-based)
            key_data: Nuevos datos de la llave
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Obtener llaves existentes
            existing_keys = self.keystore.get_keys(key_data.password)
            
            # Verificar índice
            if key_index < 1 or key_index > len(existing_keys):
                raise ValueError(f"Índice {key_index} inválido. Rango: 1-{len(existing_keys)}")
            
            # Actualizar llave
            existing_keys[key_index - 1] = key_data.key
            self.keystore.save_keys(existing_keys, key_data.password)
            
            logger.info(f"Llave {key_index} actualizada")
            return {
                "success": True,
                "message": f"Llave {key_index} actualizada correctamente",
                "total": len(existing_keys)
            }
        except Exception as e:
            logger.error(f"Error actualizando llave: {e}")
            raise
    
    def delete_key(self, key_index: int, key_data: KeyDelete) -> Dict:
        """
        Elimina una llave
        Args:
            key_index: Índice de la llave (1-based)
            key_data: Datos de eliminación
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Obtener llaves existentes
            existing_keys = self.keystore.get_keys(key_data.password)
            
            # Verificar índice
            if key_index < 1 or key_index > len(existing_keys):
                raise ValueError(f"Índice {key_index} inválido. Rango: 1-{len(existing_keys)}")
            
            # Eliminar llave
            deleted_key = existing_keys.pop(key_index - 1)
            self.keystore.save_keys(existing_keys, key_data.password)
            
            logger.info(f"Llave {key_index} eliminada")
            return {
                "success": True,
                "message": f"Llave {key_index} eliminada correctamente",
                "remaining": len(existing_keys),
                "deleted_key": deleted_key[:10] + "..."
            }
        except Exception as e:
            logger.error(f"Error eliminando llave: {e}")
            raise
    
    def reorder_keys(self, order: List[int], password: str) -> Dict:
        """
        Reordena las llaves
        Args:
            order: Nuevo orden de índices (1-based)
            password: Contraseña del admin
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Obtener llaves existentes
            existing_keys = self.keystore.get_keys(password)
            
            # Validar orden
            if len(order) != len(existing_keys):
                raise ValueError(f"El orden debe tener {len(existing_keys)} elementos")
            
            # Reordenar
            reordered_keys = [existing_keys[i - 1] for i in order]
            self.keystore.save_keys(reordered_keys, password)
            
            logger.info(f"Llaves reordenadas: {order}")
            return {
                "success": True,
                "message": "Orden actualizado correctamente",
                "new_order": order,
                "total": len(reordered_keys)
            }
        except Exception as e:
            logger.error(f"Error reordenando llaves: {e}")
            raise
    
    def bulk_add_keys(self, keys: List[str], password: str) -> Dict:
        """
        Añade múltiples llaves a la vez
        Args:
            keys: Lista de llaves a añadir
            password: Contraseña del admin
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar llaves
            for key in keys:
                # Validar formato
                if len(key) != 44:
                    raise ValueError(f"Llave inválida: {key[:10]}... (longitud {len(key)})")
                try:
                    base64.b64decode(key)
                except Exception:
                    raise ValueError(f"Base64 inválido: {key[:10]}...")
            
            # Guardar todas las llaves (reemplaza las existentes)
            self.keystore.save_keys(keys, password)
            
            logger.info(f"Guardadas {len(keys)} llaves en bulk")
            return {
                "success": True,
                "message": f"{len(keys)} llaves guardadas correctamente",
                "total": len(keys)
            }
        except Exception as e:
            logger.error(f"Error añadiendo llaves bulk: {e}")
            raise
    
    def get_settings(self) -> Dict:
        """Obtiene la configuración actual"""
        try:
            return self.keystore.get_settings()
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones: {e}")
            return {"threshold": 2, "namespace": "vault", "container_name": "vault", "monitor_interval": 30}
    
    def set_threshold(self, threshold: int, password: Optional[str] = None) -> Dict:
        """
        Configura el threshold
        Args:
            threshold: Nuevo threshold
            password: Contraseña del admin (opcional, pero recomendada)
        Returns:
            Dict: Resultado de la operación
        """
        try:
            if threshold < 1 or threshold > 10:
                raise ValueError("Threshold debe estar entre 1 y 10")
            
            self.keystore.set_threshold(threshold)
            
            logger.info(f"Threshold actualizado a {threshold}")
            return {
                "success": True,
                "message": f"Threshold actualizado a {threshold}",
                "threshold": threshold
            }
        except Exception as e:
            logger.error(f"Error configurando threshold: {e}")
            raise
    
    def get_key_count(self) -> int:
        """Obtiene el número de llaves configuradas (sin descifrar)"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.keystore.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM keys")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error obteniendo conteo de llaves: {e}")
            return 0
    
    def validate_keys_with_threshold(self, password: str) -> bool:
        """
        Verifica que hay suficientes llaves para el threshold
        Args:
            password: Contraseña del admin
        Returns:
            bool: True si hay suficientes llaves
        """
        try:
            keys = self.keystore.get_keys(password)
            threshold = self.keystore.get_threshold()
            return len(keys) >= threshold
        except Exception:
            return False