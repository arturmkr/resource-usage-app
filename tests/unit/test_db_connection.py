from unittest.mock import Mock, patch

from src import db_connection


def test_configure_database_disposes_existing_engine_and_clears_cache():
    existing_engine = Mock()

    db_connection.reset_database_configuration()
    with patch("src.db_connection.create_engine", return_value=existing_engine) as create_engine:
        assert db_connection.get_engine() is existing_engine
        db_connection.configure_database("postgresql+psycopg://user:pass@localhost:5432/resource_usage_app")

    existing_engine.dispose.assert_called_once()
    create_engine.assert_called_once()
    db_connection.reset_database_configuration()
