from abc import ABC
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.default import DB_USERNAME, DB_PASSWORD, DB_HOSTNAME, DB_PORT, DB_NAME

db_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"


@lru_cache(maxsize=None)
def get_engine():
    return create_engine(db_url)


session_factory = sessionmaker(bind=get_engine())


class DbSession(ABC):

    def __enter__(self):
        self.session: Session = session_factory()
        self.transaction = self.session.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.transaction.rollback()
        else:
            self.transaction.commit()
        self.session.close()
