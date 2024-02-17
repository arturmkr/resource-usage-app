# tests/integration/test_get_resource.py

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_get_resource_integration(create_test_resource_for_update):
    test_resource_id = create_test_resource_for_update

    response = client.get(f"/resources/{test_resource_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['id'] == str(test_resource_id)
    # Add more assertions based on the expected response


def test_get_resource_integration(simple_fixture):
    assert simple_fixture == "simple_value"
