import uuid
from datetime import datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app import app
from models.pydantic_models import ResourceOut
from resource_service import create_resource_service

client = TestClient(app)


def test_get_resource():
    mock_service = Mock()
    # Mock the service to return a valid ResourceOut object
    mock_service.get_resource.return_value = ResourceOut(
        id=uuid.uuid4(),
        resource_name="Test Resource",
        status="FREE",
        created_at="2021-01-01T00:00:00",
        tags=["test"],
        description="Test Description"
    )
    app.dependency_overrides[create_resource_service] = lambda: mock_service
    resource_id = "123e4567-e89b-12d3-a456-426614174000"

    response = client.get(f"/resources/{resource_id}")
    mock_service.get_resource.assert_called_once_with(resource_id)
    assert response.status_code == 200


def test_create_resource_endpoint():
    mock_service = Mock()
    app.dependency_overrides[create_resource_service] = lambda: mock_service

    # Prepare a mock return value for create_resource method
    mock_resource_id = uuid.uuid4()
    mock_service.create_resource.return_value = ResourceOut(
        id=mock_resource_id,
        resource_name="New Resource",
        description="A new test resource",
        tags=["new", "test"],
        status="FREE",
        created_at=datetime.now(),
        # Include other required fields as per ResourceOut model
    )

    resource_data = {
        "resource_name": "New Resource",
        "description": "A new test resource",
        "tags": ["new", "test"]
    }

    response = client.post("/resources", json=resource_data)

    assert response.status_code == 200
    mock_service.create_resource.assert_called_once()
