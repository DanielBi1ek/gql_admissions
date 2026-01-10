import logging
import uuid

from .client import createGQLClient
from src.DBFeeder import get_demodata


def _uuid_to_str(val):
    if isinstance(val, uuid.UUID):
        return str(val)
    return val


def test_client_admission_process_by_id():
    data = get_demodata()
    process = data["admission_processes"][0]
    client = createGQLClient()
    json = {
        "query": """query($id: UUID!){ result: admissionProcessById(id: $id) { id paymentId } }""",
        "variables": {
            "id": _uuid_to_str(process["id"]),
        },
    }
    headers = {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}
    response = client.post("/gql", headers=headers, json=json)
    assert response.status_code == 200
    response = response.json()
    logging.info(response)
    assert response.get("errors", None) is None
    data = response.get("data", None)
    assert data is not None
    assert data["result"]["id"] == _uuid_to_str(process["id"])


def test_client_admission_application_by_id():
    data = get_demodata()
    application = data["admission_applications"][0]
    client = createGQLClient()
    json = {
        "query": """query($id: UUID!){ result: admissionApplicationById(id: $id) { id applicantId } }""",
        "variables": {
            "id": _uuid_to_str(application["id"]),
        },
    }
    headers = {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}
    response = client.post("/gql", headers=headers, json=json)
    assert response.status_code == 200
    response = response.json()
    logging.info(response)
    assert response.get("errors", None) is None
    data = response.get("data", None)
    assert data is not None
    assert data["result"]["id"] == _uuid_to_str(application["id"])
