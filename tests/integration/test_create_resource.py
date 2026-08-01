# tests/integration/test_create_resource.py

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_create_resource_integration():
    resource_data = {
        "resource_name": "Integration Test Resource",
        "description": "A resource created during integration testing",
        "tags": ["integration", "test"],
    }

    response = client.post("/resources", json=resource_data)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["resource_name"] == resource_data["resource_name"]
    assert response_data["description"] == resource_data["description"]
    resource_id = response_data["id"]

    delete_response = client.delete(f"/resources/{resource_id}")
    assert delete_response.status_code == 200
