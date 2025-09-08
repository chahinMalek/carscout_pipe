from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.carscout_pipe.config.settings import settings
from src.carscout_pipe.infra.db.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the database engine and session factory."""
        # Ensure database directory exists
        if settings.database.path:
            db_path = Path(settings.database.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._engine = create_engine(settings.database.url, echo=settings.database.echo)
        self._session_factory = sessionmaker(bind=self._engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self._engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(self._engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session using context manager."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get a database session directly (caller must manage lifecycle)."""
        return self._session_factory()


# Global database manager instance
db_manager = DatabaseManager()
