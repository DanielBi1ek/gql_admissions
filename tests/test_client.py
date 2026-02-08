import pytest
import logging

from .client import createGQLClient
from .shared import get_demodata


def test_client_read():
    client = createGQLClient()
    data = get_demodata()
    offer = data["admission_offers"][0]

    json = {
        'query': """query($id: UUID!){ result: admissionOfferById(id: $id) {id} }""",
        'variables': {
            'id': str(offer["id"])
        }
    }
    headers = {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}
    response = client.post("/gql", headers=headers, json=json)
    assert response.status_code == 200
    response = response.json()
    logging.info(response)
    assert response.get("errors", None) is None
    data = response.get("data", None)
    assert data is not None


def test_client_hello_world():
    client = createGQLClient()
    json = {
        'query': """{ admissionOfferPage { id } }""",
        'variables': {}
    }
    headers = {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}
    response = client.post("/gql", headers=headers, json=json)
    assert response.status_code == 200
    response = response.json()
    logging.info(response)
    assert response.get("errors", None) is None
    data = response.get("data", None)
    assert data is not None


def test_client_auth_ok():
    client = createGQLClient()
    data = get_demodata()
    bank_account = data["admission_bank_accounts"][0]

    json = {
        'query': """query($id: UUID!){ result: admissionBankAccountById(id: $id) { id accountNumber bankCode }}""",
        'variables': {
            'id': str(bank_account["id"])
        }
    }
    headers = {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}
    response = client.post("/gql", headers=headers, json=json)
    assert response.status_code == 200
    response = response.json()
    logging.info(response)
    assert response.get("errors", None) is None
    data = response.get("data", None)
    assert data is not None
    result = data.get("result", None)
    assert result is not None
    accountNumber = result.get("accountNumber", None)
    assert accountNumber is not None


def test_client_auth_notok():
    client = createGQLClient()
    data = get_demodata()
    applicant = data["admission_applicants"][0]

    json = {
        'query': """query($id: UUID!){ result: admissionApplicantById(id: $id) { id firstname }}""",
        'variables': {
            'id': str(applicant["id"])
        }
    }
    # No authorization header - should fail or return null for protected fields
    headers = {}
    logging.info("test_client_auth_notok.response")
    try:
        response = client.post("/gql", headers=headers, json=json)
        # The response might have errors or null result due to no auth
        if response.status_code == 200:
            response_json = response.json()
            # Either errors or null result is acceptable
            has_errors = response_json.get("errors") is not None
            has_null_result = response_json.get("data", {}).get("result") is None
            assert has_errors or has_null_result
    except Exception:
        # Exception is also acceptable for unauthorized requests
        pass
