# tests/test_api_exceptions.py

from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.app import app
from src.exceptions import ResourceBlockException, ResourceNotFoundException, ResourceReleaseException
from src.resource_service import create_resource_service

client = TestClient(app)


def test_get_resource_not_found():
    resource_id = uuid4()
    mock_service = Mock()
    mock_service.get_resource.side_effect = ResourceNotFoundException(str(resource_id))
    app.dependency_overrides[create_resource_service] = lambda: mock_service

    response = client.get(f"/resources/{resource_id}")

    assert response.status_code == 404
    assert "not found" in response.text


def test_block_resource_exception():
    resource_id = uuid4()
    mock_service = Mock()
    mock_service.block_resource.side_effect = ResourceBlockException(str(resource_id))
    app.dependency_overrides[create_resource_service] = lambda: mock_service

    response = client.put(f"/resources/{resource_id}/block", json={"description": "Blocking attempt"})

    assert response.status_code == 409
    assert "cannot be blocked" in response.text


def test_release_resource_exception():
    resource_id = uuid4()
    lease_token = uuid4()
    mock_service = Mock()
    mock_service.release_resource.side_effect = ResourceReleaseException(str(resource_id))
    app.dependency_overrides[create_resource_service] = lambda: mock_service

    response = client.put(f"/resources/{resource_id}/release", json={"lease_token": str(lease_token)})

    assert response.status_code == 409
    assert "cannot be released" in response.text
