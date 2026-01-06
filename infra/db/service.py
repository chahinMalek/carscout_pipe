from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseService:
    def __init__(self, connection_string: str, echo: bool = False):
        self.engine = create_engine(connection_string, echo=echo, future=True)
        self.session_local = sessionmaker(bind=self.engine, autoflush=False, future=True)

    def create_session(self):
        return self.session_local()

    def create_all_tables(self, base):
        # for sqlite, ensure the directory exists
        if self.engine.url.drivername == "sqlite":
            import os
            from pathlib import Path

            db_path = self.engine.url.database
            if db_path:
                directory = os.path.dirname(db_path)
                if directory:
                    Path(directory).mkdir(parents=True, exist_ok=True)

        base.metadata.create_all(self.engine)
