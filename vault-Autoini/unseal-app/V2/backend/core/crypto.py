# core/crypto.py
import os
import base64
import sqlite3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Tuple, Optional
import json
import logging

logger = logging.getLogger(__name__)

class KeyEncryption:
    """Maneja el cifrado/descifrado de las llaves de unseal"""
    
    SALT_SIZE = 32
    NONCE_SIZE = 12
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Deriva una llave AES-256 a partir de la contraseña usando PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        return kdf.derive(password.encode('utf-8'))
    
    @staticmethod
    def encrypt_data(data: dict, password: str) -> bytes:
        """Cifra un diccionario con AES-256-GCM"""
        salt = os.urandom(KeyEncryption.SALT_SIZE)
        key = KeyEncryption.derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        plaintext = json.dumps(data).encode('utf-8')
        nonce = os.urandom(KeyEncryption.NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        return salt + nonce + ciphertext
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, password: str) -> dict:
        """Descifra los datos cifrados con AES-256-GCM"""
        try:
            salt = encrypted_data[:KeyEncryption.SALT_SIZE]
            nonce = encrypted_data[KeyEncryption.SALT_SIZE:KeyEncryption.SALT_SIZE + KeyEncryption.NONCE_SIZE]
            ciphertext = encrypted_data[KeyEncryption.SALT_SIZE + KeyEncryption.NONCE_SIZE:]
            
            key = KeyEncryption.derive_key(password, salt)
            aesgcm = AESGCM(key)
            
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error al descifrar datos: {type(e).__name__}: {str(e)}")
            logger.error(f"Tamaño de datos cifrados: {len(encrypted_data)} bytes")
            raise ValueError(f"Error al descifrar datos: {type(e).__name__}: {str(e)}")
    
    @staticmethod
    def encrypt_key(key_data: str, password: str) -> str:
        """Cifra una llave individual y la retorna como string base64"""
        encrypted = KeyEncryption.encrypt_data({"key": key_data}, password)
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_key(encrypted_key: str, password: str) -> str:
        """Descifra una llave individual desde string base64"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_key)
            data = KeyEncryption.decrypt_data(encrypted_bytes, password)
            return data["key"]
        except Exception as e:
            logger.error(f"Error descifrando llave: {e}")
            raise


class SecureKeyStore:
    """Almacén seguro para las llaves usando SQLite con cifrado"""
    
    def __init__(self, db_path: str = "/data/keys.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite con todas las tablas necesarias"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de llaves
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_index INTEGER UNIQUE NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de configuración
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    threshold INTEGER NOT NULL DEFAULT 2,
                    namespace TEXT DEFAULT 'vault',
                    container_name TEXT DEFAULT 'vault',
                    monitor_interval INTEGER DEFAULT 30,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla para la contraseña del admin (hash)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_password (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    password_hash TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla para la contraseña de unseal (texto plano, para el worker)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unseal_password (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    password TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar configuración por defecto
            cursor.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO settings (id, threshold, namespace, container_name, monitor_interval)
                    VALUES (1, 2, 'vault', 'vault', 30)
                """)
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Base de datos inicializada en: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def save_keys(self, keys: list, password: str):
        """Guarda las llaves cifradas en la base de datos"""
        if not keys:
            logger.warning("⚠️ Lista de llaves vacía, no se guardará nada")
            return
        
        encrypted_keys = []
        for idx, key in enumerate(keys, 1):
            try:
                enc_key = KeyEncryption.encrypt_key(key, password)
                encrypted_keys.append(enc_key)
                logger.info(f"✅ Llave {idx} cifrada correctamente")
            except Exception as e:
                logger.error(f"❌ Error cifrando llave {idx}: {e}")
                raise
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM keys")
        
        for idx, enc_key in enumerate(encrypted_keys, 1):
            cursor.execute(
                "INSERT INTO keys (key_index, encrypted_key) VALUES (?, ?)",
                (idx, enc_key)
            )
        
        conn.commit()
        conn.close()
        logger.info(f"✅ {len(keys)} llaves guardadas correctamente")
    
    def get_keys(self, password: str) -> list:
        """Obtiene y descifra todas las llaves"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key_index, encrypted_key FROM keys ORDER BY key_index")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logger.info("ℹ️ No hay llaves almacenadas")
            return []
        
        logger.info(f"🔍 Intentando descifrar {len(rows)} llaves...")
        
        keys = []
        failed_keys = []
        for idx, enc_key in rows:
            try:
                key = KeyEncryption.decrypt_key(enc_key, password)
                keys.append(key)
                logger.info(f"✅ Llave {idx} descifrada correctamente")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo descifrar la llave {idx}: {e}")
                failed_keys.append(idx)
                continue
        
        if failed_keys:
            logger.warning(f"⚠️ {len(failed_keys)} llaves no pudieron descifrarse: {failed_keys}")
        
        logger.info(f"✅ {len(keys)} llaves descifradas correctamente")
        return keys
    
    def reencrypt_keys(self, old_password: str, new_password: str) -> bool:
        """
        Re-cifra todas las llaves con una nueva contraseña.
        Útil cuando se cambia la contraseña del admin.
        """
        try:
            # Obtener llaves descifradas con la contraseña anterior
            keys = self.get_keys(old_password)
            if not keys:
                logger.warning("⚠️ No hay llaves para re-cifrar")
                return False
            
            # Guardar con la nueva contraseña
            self.save_keys(keys, new_password)
            logger.info(f"✅ {len(keys)} llaves re-cifradas con nueva contraseña")
            return True
        except Exception as e:
            logger.error(f"❌ Error re-cifrando llaves: {e}")
            return False
    
    def get_key_count(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keys")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_threshold(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT threshold FROM settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 2
    
    def set_threshold(self, threshold: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (id, threshold, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (threshold,))
        conn.commit()
        conn.close()
        logger.info(f"✅ Threshold actualizado a {threshold}")
    
    def get_settings(self) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT threshold, namespace, container_name, monitor_interval 
            FROM settings WHERE id = 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "threshold": row[0],
                "namespace": row[1] or "vault",
                "container_name": row[2] or "vault",
                "monitor_interval": row[3] or 30
            }
        return {"threshold": 2, "namespace": "vault", "container_name": "vault", "monitor_interval": 30}
    
    def save_settings(self, settings: dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (id, threshold, namespace, container_name, monitor_interval, updated_at)
            VALUES (1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            settings.get("threshold", 2),
            settings.get("namespace", "vault"),
            settings.get("container_name", "vault"),
            settings.get("monitor_interval", 30)
        ))
        conn.commit()
        conn.close()
        logger.info("✅ Configuraciones guardadas")
    
    # ========== MÉTODOS PARA ADMIN PASSWORD ==========
    
    def save_admin_password_hash(self, password_hash: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO admin_password (id, password_hash, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (password_hash,))
        conn.commit()
        conn.close()
        logger.info("✅ Hash de admin guardado en base de datos")
    
    def get_admin_password_hash(self) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admin_password WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    # ========== MÉTODOS PARA UNSEAL PASSWORD ==========
    
    def save_unseal_password(self, password: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO unseal_password (id, password, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (password,))
        conn.commit()
        conn.close()
        logger.info("✅ Contraseña de unseal guardada en base de datos")
    
    def get_unseal_password(self) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM unseal_password WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def test_unseal_password(self, password: str) -> bool:
        """Prueba si la contraseña puede descifrar las llaves"""
        try:
            keys = self.get_keys(password)
            return len(keys) > 0
        except Exception as e:
            logger.warning(f"⚠️ Prueba de contraseña falló: {e}")
            return False