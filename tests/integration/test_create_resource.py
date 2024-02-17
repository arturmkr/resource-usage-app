# tests/integration/test_create_resource.py

import json

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_create_resource_integration():
    resource_data = {
        "resource_name": "Integration Test Resource",
        "description": "A resource created during integration testing",
        "tags": ["integration", "test"]
    }

    response = client.post("/resources", content=json.dumps(resource_data))

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['resource_name'] == resource_data['resource_name']
    assert response_data['description'] == resource_data['description']
    # Add more assertions as needed

    resource_id = response_data['id']

    # Optionally, clean up by deleting the created resource
    delete_response = client.delete(f"/resources/{resource_id}")
    assert delete_response.status_code == 200
