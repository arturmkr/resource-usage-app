from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.default import DB_USERNAME, DB_PASSWORD, DB_HOSTNAME, DB_PORT, DB_NAME

db_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"


@lru_cache(maxsize=None)
def get_engine():
    return create_engine(db_url)


session_factory = sessionmaker(bind=get_engine())


@contextmanager
def get_db_session():
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
