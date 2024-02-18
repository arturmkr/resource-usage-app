# tests/integration/test_update_resource.py

import json

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_update_resource_integration(create_test_resource_for_update):
    test_resource_id = create_test_resource_for_update
    update_data = {
        "description": "Updated description"
    }

    response = client.put(f"/resources/{test_resource_id}/block", content=json.dumps(update_data))

    assert response.status_code == 200
    # Verify the resource was updated
    # Fetch the resource and assert the changes
