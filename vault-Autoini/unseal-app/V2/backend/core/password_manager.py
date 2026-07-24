# core/password_manager.py
import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import re

from core.database import engine, AsyncSessionLocal, SystemState, WorkerPassword
from core.crypto import SecureKeyStore
from sqlalchemy import select

logger = logging.getLogger(__name__)

class PasswordManager:
    """
    Gestor de contraseñas del sistema.
    Maneja contraseñas temporales, cambios y sincronización.
    """
    
    SYSTEM_SECRET = os.getenv("SYSTEM_SECRET", os.urandom(32).hex())
    SALT_SIZE = 32
    NONCE_SIZE = 12
    
    def __init__(self):
        self.keystore = SecureKeyStore()
        
    # ============ VALIDACIÓN DE CONTRASEÑA ============
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Valida la fortaleza de la contraseña según políticas.
        Returns: (es_válida, mensaje_error)
        """
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if len(password) > 72:
            return False, "La contraseña no puede tener más de 72 caracteres"
        
        # Al menos una mayúscula
        if not re.search(r'[A-Z]', password):
            return False, "Debe contener al menos una mayúscula"
        
        # Al menos una minúscula
        if not re.search(r'[a-z]', password):
            return False, "Debe contener al menos una minúscula"
        
        # Al menos un número
        if not re.search(r'[0-9]', password):
            return False, "Debe contener al menos un número"
        
        # Al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Debe contener al menos un carácter especial"
        
        # No puede ser igual a la anterior (historial)
        return True, "Contraseña válida"
    
    # ============ GESTIÓN DE CONTRASEÑA TEMPORAL ============
    
    async def is_temporary_password(self) -> bool:
        """Verifica si la contraseña actual es temporal (no cambiada)"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SystemState).where(SystemState.id == 1)
            )
            state = result.scalar_one_or_none()
            
            if not state:
                # Primera ejecución
                return True
            
            return not state.password_changed
    
    async def mark_password_changed(self):
        """Marca que la contraseña ya fue cambiada"""
        async with AsyncSessionLocal() as session:
            state = await session.execute(
                select(SystemState).where(SystemState.id == 1)
            )
            state = state.scalar_one_or_none()
            
            if not state:
                state = SystemState(id=1)
                session.add(state)
            
            state.password_changed = True
            state.first_login_done = True
            state.last_password_change = datetime.utcnow()
            await session.commit()
            logger.info("✅ Contraseña marcada como cambiada")
    
    async def add_to_password_history(self, password_hash: str):
        """Añade un hash al historial para evitar reuso"""
        async with AsyncSessionLocal() as session:
            state = await session.execute(
                select(SystemState).where(SystemState.id == 1)
            )
            state = state.scalar_one_or_none()
            
            if not state:
                state = SystemState(id=1)
                session.add(state)
            
            history = json.loads(state.password_history or '[]')
            history.append({
                "hash": password_hash,
                "changed_at": datetime.utcnow().isoformat()
            })
            
            # Mantener solo los últimos 5 cambios
            if len(history) > 5:
                history = history[-5:]
            
            state.password_history = json.dumps(history)
            await session.commit()
    
    async def check_password_reuse(self, password_hash: str) -> bool:
        """Verifica si la contraseña ya fue usada antes"""
        async with AsyncSessionLocal() as session:
            state = await session.execute(
                select(SystemState).where(SystemState.id == 1)
            )
            state = state.scalar_one_or_none()
            
            if not state or not state.password_history:
                return False
            
            history = json.loads(state.password_history)
            
            # Comparar con los hashes anteriores
            for entry in history:
                if entry["hash"] == password_hash:
                    return True
            
            return False
    
    # ============ CIFRADO DE CONTRASEÑA PARA WORKER ============
    
    def _derive_worker_key(self, salt: bytes) -> bytes:
        """Deriva clave para cifrar la contraseña del worker"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.SYSTEM_SECRET.encode())
    
    async def save_worker_password(self, password: str):
        """
        Guarda la contraseña del worker cifrada con SYSTEM_SECRET.
        Esto permite que el worker pueda obtener la contraseña sin almacenarla en texto plano.
        """
        try:
            # Generar salt aleatorio
            salt = os.urandom(self.SALT_SIZE)
            
            # Derivar clave del sistema
            key = self._derive_worker_key(salt)
            
            # Cifrar la contraseña
            aesgcm = AESGCM(key)
            nonce = os.urandom(self.NONCE_SIZE)
            ciphertext = aesgcm.encrypt(
                nonce,
                password.encode(),
                None
            )
            
            # Codificar para almacenamiento
            encrypted_data = salt + nonce + ciphertext
            encrypted_b64 = base64.b64encode(encrypted_data).decode()
            
            async with AsyncSessionLocal() as session:
                worker_pwd = await session.execute(
                    select(WorkerPassword).where(WorkerPassword.id == 1)
                )
                worker_pwd = worker_pwd.scalar_one_or_none()
                
                if not worker_pwd:
                    worker_pwd = WorkerPassword(id=1)
                    session.add(worker_pwd)
                
                worker_pwd.encrypted_password = encrypted_b64
                worker_pwd.salt = base64.b64encode(salt).decode()
                worker_pwd.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info("✅ Contraseña del worker guardada cifrada")
                
        except Exception as e:
            logger.error(f"❌ Error guardando contraseña del worker: {e}")
            raise
    
    async def get_worker_password(self) -> Optional[str]:
        """
        Obtiene la contraseña del worker descifrada.
        Returns: contraseña en texto plano o None si no existe
        """
        try:
            async with AsyncSessionLocal() as session:
                worker_pwd = await session.execute(
                    select(WorkerPassword).where(WorkerPassword.id == 1)
                )
                worker_pwd = worker_pwd.scalar_one_or_none()
                
                if not worker_pwd or not worker_pwd.encrypted_password:
                    return None
                
                # Decodificar
                encrypted_data = base64.b64decode(worker_pwd.encrypted_password)
                salt = encrypted_data[:self.SALT_SIZE]
                nonce = encrypted_data[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
                ciphertext = encrypted_data[self.SALT_SIZE + self.NONCE_SIZE:]
                
                # Derivar clave
                key = self._derive_worker_key(salt)
                
                # Descifrar
                aesgcm = AESGCM(key)
                password = aesgcm.decrypt(nonce, ciphertext, None)
                
                return password.decode()
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo contraseña del worker: {e}")
            return None
    
    # ============ RE-CIFRADO DE LLAVES ============
    
    async def reencrypt_all_keys(self, old_password: str, new_password: str) -> bool:
        """
        Re-cifra TODAS las llaves con la nueva contraseña.
        Implementa verificación y rollback en caso de error.
        """
        try:
            # 1. Obtener llaves con contraseña actual
            logger.info("🔍 Obteniendo llaves con contraseña actual...")
            old_keys = self.keystore.get_keys(old_password)
            
            if not old_keys:
                logger.warning("⚠️ No hay llaves para re-cifrar")
                return False
            
            logger.info(f"📦 {len(old_keys)} llaves obtenidas")
            
            # 2. Backup de las llaves cifradas actuales
            logger.info("💾 Creando backup de llaves cifradas...")
            backup_keys = self.keystore.get_encrypted_keys()  # Nuevo método
            
            # 3. Re-cifrar con nueva contraseña
            logger.info(f"🔐 Re-cifrando {len(old_keys)} llaves con nueva contraseña...")
            self.keystore.save_keys(old_keys, new_password)
            
            # 4. VERIFICAR: descifrar con nueva contraseña
            logger.info("✅ Verificando re-cifrado...")
            test_keys = self.keystore.get_keys(new_password)
            
            if test_keys and len(test_keys) == len(old_keys):
                logger.info(f"✅ Re-cifrado exitoso: {len(test_keys)} llaves verificadas")
                
                # 5. Actualizar contraseña del worker
                await self.save_worker_password(new_password)
                
                return True
            else:
                # 6. Rollback en caso de error
                logger.error(f"❌ Falló verificación: {len(test_keys)}/{len(old_keys)} llaves")
                logger.info("🔄 Haciendo rollback de llaves cifradas...")
                self.keystore.restore_encrypted_keys(backup_keys)  # Nuevo método
                return False
                
        except Exception as e:
            logger.error(f"❌ Error re-cifrando llaves: {e}")
            return False