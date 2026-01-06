from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base


class SQLiteSafeDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value == "":
            return None
        return value


Base = declarative_base()
