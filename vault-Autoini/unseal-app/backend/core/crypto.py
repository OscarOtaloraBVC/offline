import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Tuple
import json

class KeyEncryption:
    """Maneja el cifrado/descifrado de las llaves de unseal"""
    
    SALT_SIZE = 32
    NONCE_SIZE = 12
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Deriva una llave AES-256 a partir de la contraseña usando PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits para AES-256
            salt=salt,
            iterations=600000,  # Alta iteración para seguridad
        )
        return kdf.derive(password.encode('utf-8'))
    
    @staticmethod
    def encrypt_data(data: dict, password: str) -> bytes:
        """
        Cifra un diccionario con AES-256-GCM
        Retorna: salt + nonce + ciphertext + tag
        """
        salt = os.urandom(KeyEncryption.SALT_SIZE)
        key = KeyEncryption.derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        # Convertir data a JSON y luego a bytes
        plaintext = json.dumps(data).encode('utf-8')
        
        # Generar nonce y cifrar
        nonce = os.urandom(KeyEncryption.NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Concatenar: salt + nonce + ciphertext
        return salt + nonce + ciphertext
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, password: str) -> dict:
        """Descifra los datos cifrados con AES-256-GCM"""
        # Extraer salt, nonce y ciphertext
        salt = encrypted_data[:KeyEncryption.SALT_SIZE]
        nonce = encrypted_data[KeyEncryption.SALT_SIZE:KeyEncryption.SALT_SIZE + KeyEncryption.NONCE_SIZE]
        ciphertext = encrypted_data[KeyEncryption.SALT_SIZE + KeyEncryption.NONCE_SIZE:]
        
        # Derivar key y descifrar
        key = KeyEncryption.derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Error al descifrar datos: {e}")
    
    @staticmethod
    def encrypt_key(key_data: str, password: str) -> str:
        """Cifra una llave individual y la retorna como string base64"""
        encrypted = KeyEncryption.encrypt_data({"key": key_data}, password)
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_key(encrypted_key: str, password: str) -> str:
        """Descifra una llave individual desde string base64"""
        encrypted_bytes = base64.b64decode(encrypted_key)
        data = KeyEncryption.decrypt_data(encrypted_bytes, password)
        return data["key"]

class SecureKeyStore:
    """Almacén seguro para las llaves usando SQLite con cifrado"""
    
    def __init__(self, db_path: str = "keys.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_index INTEGER UNIQUE NOT NULL,
                encrypted_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        conn.commit()
        conn.close()
    
    def save_keys(self, keys: list, password: str):
        """Guarda las llaves cifradas en la base de datos"""
        import sqlite3
        
        # Cifrar cada llave
        encrypted_keys = [
            KeyEncryption.encrypt_key(key, password) 
            for key in keys
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Limpiar llaves existentes
        cursor.execute("DELETE FROM keys")
        
        # Insertar nuevas llaves
        for idx, enc_key in enumerate(encrypted_keys, 1):
            cursor.execute(
                "INSERT INTO keys (key_index, encrypted_key) VALUES (?, ?)",
                (idx, enc_key)
            )
        
        conn.commit()
        conn.close()
    
    def get_keys(self, password: str) -> list:
        """Obtiene y descifra todas las llaves"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key_index, encrypted_key FROM keys ORDER BY key_index")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Descifrar cada llave
        keys = []
        for idx, enc_key in rows:
            try:
                key = KeyEncryption.decrypt_key(enc_key, password)
                keys.append(key)
            except Exception:
                # Si una llave no se puede descifrar, omitir
                continue
        
        return keys
    
    def get_threshold(self) -> int:
        """Obtiene el threshold configurado"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT threshold FROM settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else 2
    
    def set_threshold(self, threshold: int):
        """Configura el threshold"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO settings (id, threshold, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (threshold,))
        
        conn.commit()
        conn.close()
    
    def get_settings(self) -> dict:
        """Obtiene todas las configuraciones"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
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