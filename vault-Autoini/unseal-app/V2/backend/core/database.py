from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text
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