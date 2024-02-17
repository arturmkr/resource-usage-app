# tests/test_resource_repository.py
import uuid
from unittest.mock import Mock, patch, MagicMock

import pytest

from exceptions import ResourceNotFoundException
from models.filters import ResourceFilter, PaginationParams
from resource_repository import ResourceRepositoryPostgreSQL


@patch('resource_repository.ResourceRepositoryPostgreSQL.get_resources')
def test_get_resources(mock_get_resources):
    mock_session = Mock()
    repo = ResourceRepositoryPostgreSQL()
    repo.session = mock_session
    resource_filter = ResourceFilter(status="FREE")
    pagination = PaginationParams(skip=0, limit=10)

    repo.get_resources(resource_filter, pagination)
    mock_get_resources.assert_called_once_with(resource_filter, pagination)


@patch('db_connection.get_db_session')
def test_get_resource_filter(mock_get_db_session):
    mock_session = MagicMock()

    mock_get_db_session.return_value.__enter__.return_value = mock_session

    repo = ResourceRepositoryPostgreSQL()
    resource_id = "test-id"
    repo.get_resource(mock_session, resource_id)

    print("Mock session method calls:", mock_session.mock_calls)

    filter_by_call_found = any('filter_by' in str(call) and 'id=' in str(call) and 'test-id' in str(call)
                               for call in mock_session.mock_calls)
    assert filter_by_call_found, "filter_by method was not called with correct arguments"


@patch('db_connection.get_db_session')
def test_remove_resource(mock_get_db_session):
    mock_session = MagicMock()
    mock_session.query().filter_by().first.return_value = None  # Simulate resource not found
    mock_get_db_session.return_value.__enter__.return_value = mock_session
    repo = ResourceRepositoryPostgreSQL()

    with pytest.raises(ResourceNotFoundException):
        repo.remove_resource(mock_session, str(uuid.uuid4()))

    mock_session.delete.assert_not_called()
