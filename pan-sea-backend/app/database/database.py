# app/database/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Create async engine for async operations
# Convert postgresql:// to postgresql+asyncpg:// for async operations
async_database_url = settings.database_url_async.replace('postgresql://', 'postgresql+asyncpg://')
async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,
    pool_recycle=300
)

# Create sync engine for sync operations (if needed)
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False
)

class DatabaseManager:
    """Database manager using SQLAlchemy ORM"""
    
    def __init__(self):
        self.async_engine = async_engine
        self.sync_engine = sync_engine
    
    async def get_async_session(self) -> AsyncSession:
        """Get async database session"""
        async with AsyncSessionLocal() as session:
            return session
    
    def get_sync_session(self):
        """Get sync database session"""
        return SyncSessionLocal()
    
    async def create_tables(self):
        """Create all tables defined in models"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def execute_query(self, query: str, *params):
        """Execute a SELECT query and return results"""
        try:
            async with AsyncSessionLocal() as session:
                # Convert params tuple to list for SQLAlchemy
                params_list = list(params)
                # Create a dictionary with named parameters for SQLAlchemy
                params_dict = {f"param_{i}": param for i, param in enumerate(params_list)}
                # Replace $1, $2, etc. with :param_0, :param_1, etc.
                modified_query = query
                for i in range(len(params_list) - 1, -1, -1):
                    modified_query = modified_query.replace(f"${i+1}", f":param_{i}")
                
                result = await session.execute(text(modified_query), params_dict)
                rows = result.fetchall()
                # Convert rows to list of dictionaries
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    async def execute_command(self, query: str, *params):
        """Execute an INSERT, UPDATE, or DELETE command and return affected row count"""
        try:
            async with AsyncSessionLocal() as session:
                # Convert params tuple to list for SQLAlchemy
                params_list = list(params)
                # Create a dictionary with named parameters for SQLAlchemy
                params_dict = {f"param_{i}": param for i, param in enumerate(params_list)}
                # Replace $1, $2, etc. with :param_0, :param_1, etc.
                modified_query = query
                for i in range(len(params_list) - 1, -1, -1):
                    modified_query = modified_query.replace(f"${i+1}", f":param_{i}")
                
                result = await session.execute(text(modified_query), params_dict)
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            raise
    
    async def execute_insert_with_returning(self, query: str, *params):
        """Execute an INSERT query with RETURNING clause and return the inserted row"""
        try:
            async with AsyncSessionLocal() as session:
                # Convert params tuple to list for SQLAlchemy
                params_list = list(params)
                # Create a dictionary with named parameters for SQLAlchemy
                params_dict = {f"param_{i}": param for i, param in enumerate(params_list)}
                # Replace $1, $2, etc. with :param_0, :param_1, etc.
                modified_query = query
                for i in range(len(params_list) - 1, -1, -1):
                    modified_query = modified_query.replace(f"${i+1}", f":param_{i}")
                
                result = await session.execute(text(modified_query), params_dict)
                await session.commit()
                rows = result.fetchall()
                # Convert rows to list of dictionaries
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Error executing insert with returning: {str(e)}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()