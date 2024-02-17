# tests/test_resource_pagination.py

from unittest.mock import MagicMock, patch

from models.filters import PaginationParams, ResourceFilter
from resource_repository import ResourceRepositoryPostgreSQL


@patch('db_connection.get_db_session')
def test_resource_pagination(mock_get_db_session):
    mock_session = MagicMock()
    mock_get_db_session.return_value.__enter__.return_value = mock_session

    repo = ResourceRepositoryPostgreSQL()

    # Use a dummy ResourceFilter for testing
    resource_filter = ResourceFilter(status=None, tags=None)
    pagination_params = PaginationParams(skip=0, limit=5)

    # Mock the session's query method to return a list of mock resources
    mock_resources = [MagicMock() for _ in range(5)]

    # Setup method chaining mock
    mock_query_chain = mock_session.query.return_value
    mock_query_chain.options.return_value = mock_query_chain
    mock_query_chain.offset.return_value = mock_query_chain
    mock_query_chain.limit.return_value = mock_query_chain
    mock_query_chain.all.return_value = mock_resources

    resources = repo.get_resources(mock_session, resource_filter, pagination_params)

    # Assertions
    assert len(resources) == 5
    mock_session.query.assert_called()
