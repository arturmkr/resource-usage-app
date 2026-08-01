from contextlib import contextmanager
from functools import cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config.default import get_settings

_database_url_override: str | None = None


@cache
def get_engine():
    return create_engine(_database_url_override or get_settings().database_url, pool_pre_ping=True)


def configure_database(database_url: str) -> None:
    global _database_url_override

    if get_engine.cache_info().currsize:
        get_engine().dispose()
    _database_url_override = database_url
    get_engine.cache_clear()


def reset_database_configuration() -> None:
    global _database_url_override

    if get_engine.cache_info().currsize:
        get_engine().dispose()
    _database_url_override = None
    get_engine.cache_clear()


@contextmanager
def get_db_session():
    session = Session(get_engine(), expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
