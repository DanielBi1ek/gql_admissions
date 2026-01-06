import logging

from .client import createGQLClient


def test_client_admission_process_by_id():
    client = createGQLClient()
    json = {
        "query": """query($id: UUID!){ result: admissionProcessById(id: $id) { id name } }""",
        "variables": {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
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
    assert data["result"]["id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_client_admission_application_by_id():
    client = createGQLClient()
    json = {
        "query": """query($id: UUID!){ result: admissionApplicationById(id: $id) { id applicantName } }""",
        "variables": {
            "id": "70520d39-a157-4874-b3c8-96a9a6d6795b",
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
    assert data["result"]["id"] == "70520d39-a157-4874-b3c8-96a9a6d6795b"
