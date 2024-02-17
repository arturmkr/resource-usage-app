# tests/test_resource_history_repository.py

from unittest.mock import MagicMock, patch

from models.db_models import ResourceHistory
from resource_history_repository import ResourceHistoryRepositoryPostgreSQL


@patch('db_connection.get_db_session')
def test_add_history(mock_get_db_session):
    mock_session = MagicMock()
    mock_get_db_session.return_value.__enter__.return_value = mock_session
    repo = ResourceHistoryRepositoryPostgreSQL()

    history_entry = ResourceHistory(id="1234", operation="BLOCK", description="Test Block")
    repo.add(mock_session, history_entry)

    mock_session.add.assert_called_once_with(history_entry)
    # Remove the assertion for commit as it's not part of the add method
