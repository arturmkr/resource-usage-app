# tests/test_resource_service.py
import uuid
from datetime import datetime
from unittest.mock import Mock

from models.pydantic_models import ResourceIn
from resource_service import PgResourceService


def test_create_resource():
    mock_repo = Mock()
    service = PgResourceService()
    service.resource_repository = mock_repo
    resource_data = ResourceIn(resource_name="Test Resource", description="Test Description", tags=["test"])

    # Create a mock return value for create_resource
    mock_resource = Mock()
    mock_resource.variables = []  # Set variables to an empty list or a list of mocks
    mock_resource.to_dict.return_value = {
        'id': uuid.uuid4(),
        'resource_name': 'Test Resource',
        'description': 'Test Description',
        'tags': ['test'],
        'variables': [],
        'created_at': datetime.now(),  # Add the missing created_at field
        # Add other necessary fields from your Resource model
    }
    mock_repo.create_resource.return_value = mock_resource

    service.create_resource(resource_data)

    # Assert that create_resource was called with the expected parameters
    mock_repo.create_resource.assert_called_once()
