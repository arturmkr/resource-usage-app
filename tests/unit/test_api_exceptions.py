# tests/test_api_exceptions.py

from unittest.mock import Mock

from fastapi.testclient import TestClient

from app import app
from exceptions import ResourceNotFoundException
from resource_service import create_resource_service

client = TestClient(app)


def test_get_resource_not_found():
    mock_service = Mock()
    mock_service.get_resource.side_effect = ResourceNotFoundException("1")
    app.dependency_overrides[create_resource_service] = lambda: mock_service

    response = client.get("/resources/1")

    assert response.status_code == 404
    assert "not found" in response.text