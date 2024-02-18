import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.models.db_models import Resource
from src.resource_repository import ResourceRepositoryPostgreSQL


@pytest.fixture
def mock_db_session():
    with patch('src.db_connection.get_db_session') as mock:
        mock_session = MagicMock()
        mock.return_value.__enter__.return_value = mock_session
        yield mock_session


def test_update_resource(mock_db_session):
    # Instantiate the repository
    repo = ResourceRepositoryPostgreSQL()

    # Create a test resource
    resource_id = uuid.uuid4()
    updated_resource = Resource(id=resource_id, resource_name="Updated Name")

    # Mock the existing resource in the database
    existing_resource = MagicMock()
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = existing_resource

    # Call the method under test
    repo.update(mock_db_session, updated_resource)

    # Assertions to verify that the correct methods were called on the mock session
    mock_db_session.query.assert_called_with(Resource)
    mock_db_session.query.return_value.filter_by.assert_called_with(id=resource_id)

    # Check if the existing resource's attributes are updated correctly
    assert existing_resource.resource_name == "Updated Name"
