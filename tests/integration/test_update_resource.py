# tests/integration/test_update_resource.py

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_update_resource_integration(create_test_resource_for_update):
    test_resource_id = create_test_resource_for_update
    update_data = {"description": "Updated description"}

    response = client.put(f"/resources/{test_resource_id}/block", json=update_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == str(test_resource_id)
    assert response_data["status"] == "BLOCKED"
    assert response_data["lease_token"]
    assert response_data["lease_expires_at"]
