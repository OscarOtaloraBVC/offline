# core/database.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean  # ✅ Añadir Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./keys.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class EncryptedKey(Base):
    __tablename__ = "keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_index = Column(Integer, unique=True, nullable=False)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, default=1)
    threshold = Column(Integer, nullable=False, default=2)
    namespace = Column(String(255), default="vault")
    container_name = Column(String(255), default="vault")
    monitor_interval = Column(Integer, default=30)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class SystemState(Base):
    """Estado del sistema para gestión de contraseñas temporales"""
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True, default=1)
    password_changed = Column(Boolean, default=False)  # ✅ Ahora Boolean está importado
    first_login_done = Column(Boolean, default=False)  # ✅ Ahora Boolean está importado
    last_password_change = Column(DateTime, default=datetime.datetime.utcnow)
    password_history = Column(Text, default='[]')  # JSON con hashes anteriores
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class WorkerPassword(Base):
    """Contraseña cifrada para el worker (encriptada con secreto del sistema)"""
    __tablename__ = "worker_password"
    
    id = Column(Integer, primary_key=True, default=1)
    encrypted_password = Column(Text, nullable=False)  # Cifrada con SYSTEM_SECRET
    salt = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

async def init_db():
    """Inicializa la base de datos y crea las tablas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Verificar que existe la configuración por defecto
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        stmt = select(Settings)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = Settings()
            session.add(settings)
            await session.commit()