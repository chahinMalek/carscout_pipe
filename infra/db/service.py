from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseService:
    def __init__(self, connection_string: str, echo: bool = False):
        self.engine = create_engine(connection_string, echo=echo)
        self.session_local = sessionmaker(bind=self.engine, autoflush=False)

    def create_session(self):
        return self.session_local()

    def create_all_tables(self, base):
        pass
