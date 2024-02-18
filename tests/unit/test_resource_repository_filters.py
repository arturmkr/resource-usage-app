from unittest.mock import MagicMock

from src.models.db_models import Resource
from src.models.filters import ResourceFilter, PaginationParams
from src.resource_repository import ResourceRepositoryPostgreSQL


def test_apply_filters():
    repo = ResourceRepositoryPostgreSQL()
    mock_session = MagicMock()
    resource_filter = ResourceFilter(status="BLOCKED")
    pagination = PaginationParams(skip=0, limit=10)

    # Set up method chaining for the mock
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []

    repo.get_resources(mock_session, resource_filter, pagination)

    filter_arg = mock_query.filter.call_args[0][0]
    assert str(filter_arg) == str(Resource.status == "BLOCKED")
