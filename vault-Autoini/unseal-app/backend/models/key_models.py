from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class KeyBase(BaseModel):
    """Modelo base para llaves de unseal"""
    key: str = Field(..., min_length=44, max_length=44, description="Llave de unseal en base64")
    key_index: Optional[int] = Field(None, description="Índice de la llave (1-based)")
    
    @validator('key')
    def validate_key_format(cls, v):
        """Valida el formato de la llave (base64 de 44 caracteres)"""
        import base64
        
        # Verificar longitud
        if len(v) != 44:
            raise ValueError(f"La llave debe tener 44 caracteres, tiene {len(v)}")
        
        # Verificar que es base64 válido
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError("La llave debe ser base64 válido")
        
        return v
    
    @validator('key')
    def validate_key_no_whitespace(cls, v):
        """Verifica que la llave no tenga espacios en blanco"""
        if re.search(r'\s', v):
            raise ValueError("La llave no debe contener espacios en blanco")
        return v

class KeyCreate(KeyBase):
    """Modelo para crear una nueva llave"""
    password: str = Field(..., min_length=4, description="Contraseña del admin para cifrar")

class KeyUpdate(KeyBase):
    """Modelo para actualizar una llave existente"""
    password: str = Field(..., min_length=4, description="Contraseña del admin")
    old_password: Optional[str] = Field(None, description="Contraseña antigua si se está cambiando")

class KeyDelete(BaseModel):
    """Modelo para eliminar una llave"""
    password: str = Field(..., min_length=4, description="Contraseña del admin")

class KeyResponse(BaseModel):
    """Respuesta con información de llaves"""
    keys: List[str] = Field(..., description="Lista de llaves (en texto plano)")
    count: int = Field(..., description="Número total de llaves")
    threshold: int = Field(..., description="Número de llaves requeridas para unseal")
    encrypted_count: Optional[int] = Field(None, description="Número de llaves cifradas en almacén")

class KeyReorder(BaseModel):
    """Modelo para reordenar llaves"""
    order: List[int] = Field(..., description="Nuevo orden de índices (1-based)")
    password: str = Field(..., min_length=4, description="Contraseña del admin")
    
    @validator('order')
    def validate_order(cls, v):
        """Valida que el orden sea una permutación válida"""
        if len(v) < 1:
            raise ValueError("Debe haber al menos una llave")
        
        # Verificar que todos los índices son únicos y están en el rango correcto
        if len(set(v)) != len(v):
            raise ValueError("El orden contiene índices duplicados")
        
        # Verificar que los índices son consecutivos desde 1
        sorted_order = sorted(v)
        if sorted_order != list(range(1, len(v) + 1)):
            raise ValueError("El orden debe ser una permutación de 1..N")
        
        return v

class KeyBulkCreate(BaseModel):
    """Modelo para crear múltiples llaves"""
    keys: List[str] = Field(..., min_items=1, description="Lista de llaves")
    password: str = Field(..., min_length=4, description="Contraseña del admin")
    
    @validator('keys', each_item=True)
    def validate_key_list(cls, v):
        """Valida cada llave en la lista"""
        import base64
        
        if len(v) != 44:
            raise ValueError(f"La llave debe tener 44 caracteres, tiene {len(v)}")
        
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError("La llave debe ser base64 válido")
        
        return v

class KeyOperationResponse(BaseModel):
    """Respuesta para operaciones con llaves"""
    success: bool
    message: str
    total_keys: Optional[int] = None
    keys_affected: Optional[int] = None
    error: Optional[str] = None