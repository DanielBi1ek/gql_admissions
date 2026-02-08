"""
Integration tests for Admission GraphQL Queries.

These tests run against the actual Docker stack with Apollo.
Make sure your Docker stack is running before executing these tests.

Run with: pytest tests/test_integration_queries.py -v -m integration
"""
import pytest
import os

from .client import createFederationClient

# Configuration - adjust these to match your environment
GQL_URL = os.environ.get("GQL_URL", "http://localhost:33001/api/gql")
TEST_USERNAME = os.environ.get("TEST_USERNAME", "john.newbie@world.com")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "john.newbie@world.com")


def get_gql_client():
    """Create an authenticated GraphQL client."""
    return createFederationClient(
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        gqlurl=GQL_URL
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_offer_page():
    """Test fetching admission offers."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionOfferPage {
                id
                programId
                applicationStartDate
                applicationEndDate
            }
        }
    """

    result = await gql_client(query, {})

    # Check for errors
    if isinstance(result, dict) and "errors" in result:
        print(f"GraphQL errors: {result['errors']}")

    assert isinstance(result, dict)
    assert "data" in result
    offers = result["data"].get("admissionOfferPage")
    print(f"Found {len(offers) if offers else 0} offers")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_applicant_page():
    """Test fetching applicant page as authenticated user."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionApplicantPage {
                id
                firstname
                lastname
                applicantUserId
            }
        }
    """

    result = await gql_client(query, {})

    if isinstance(result, dict) and "errors" in result:
        print(f"GraphQL errors: {result['errors']}")
        pytest.skip("Cannot fetch applicant page - check authentication")

    assert isinstance(result, dict)
    assert "data" in result
    applicants = result["data"].get("admissionApplicantPage", [])
    print(f"Found {len(applicants)} applicants")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_applicant_by_id_owner():
    """Test fetching applicant by ID as the owner."""
    gql_client = get_gql_client()

    # First, get the current user's applicant profile
    page_query = """
        query {
            admissionApplicantPage {
                id
                firstname
                lastname
            }
        }
    """

    page_result = await gql_client(page_query, {})

    if isinstance(page_result, dict) and "errors" in page_result:
        pytest.skip("Cannot fetch applicant page")

    applicants = page_result.get("data", {}).get("admissionApplicantPage", [])
    if not applicants:
        pytest.skip("No applicants found for current user")

    # Now fetch the specific applicant by ID
    applicant_id = applicants[0]["id"]

    query = """
        query($id: UUID!) {
            admissionApplicantById(id: $id) {
                id
                firstname
                lastname
            }
        }
    """

    result = await gql_client(query, {"id": applicant_id})

    assert isinstance(result, dict)
    assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
    assert result["data"]["admissionApplicantById"] is not None
    assert result["data"]["admissionApplicantById"]["id"] == applicant_id
    print(f"Successfully fetched applicant: {result['data']['admissionApplicantById']}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_application_page():
    """Test fetching application page as authenticated user."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionApplicationPage {
                id
                applicantId
                accepted
                withdrawn
            }
        }
    """

    result = await gql_client(query, {})

    if isinstance(result, dict) and "errors" in result:
        print(f"GraphQL errors: {result['errors']}")
        pytest.skip("Cannot fetch application page")

    assert isinstance(result, dict)
    assert "data" in result
    applications = result["data"].get("admissionApplicationPage", [])
    print(f"Found {len(applications)} applications")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_application_by_id_owner():
    """Test fetching application by ID as the owner."""
    gql_client = get_gql_client()

    # First, get the current user's applications
    page_query = """
        query {
            admissionApplicationPage {
                id
                applicantId
                accepted
                withdrawn
            }
        }
    """

    page_result = await gql_client(page_query, {})

    if isinstance(page_result, dict) and "errors" in page_result:
        pytest.skip("Cannot fetch application page")

    applications = page_result.get("data", {}).get("admissionApplicationPage", [])
    if not applications:
        pytest.skip("No applications found for current user")

    # Now fetch the specific application by ID
    application_id = applications[0]["id"]

    query = """
        query($id: UUID!) {
            admissionApplicationById(id: $id) {
                id
                accepted
                withdrawn
            }
        }
    """

    result = await gql_client(query, {"id": application_id})

    assert isinstance(result, dict)
    assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
    assert result["data"]["admissionApplicationById"] is not None
    assert result["data"]["admissionApplicationById"]["id"] == application_id
    print(f"Successfully fetched application: {result['data']['admissionApplicationById']}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_bank_account_page():
    """Test fetching bank accounts."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionBankAccountPage {
                id
                accountNumber
                bankCode
            }
        }
    """

    result = await gql_client(query, {})

    assert isinstance(result, dict)
    assert "data" in result
    accounts = result["data"].get("admissionBankAccountPage", [])
    print(f"Found {len(accounts)} bank accounts")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_payment_info_page():
    """Test fetching payment infos."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionPaymentInfoPage {
                id
                requiredAmount
            }
        }
    """

    result = await gql_client(query, {})

    assert isinstance(result, dict)
    assert "data" in result
    infos = result["data"].get("admissionPaymentInfoPage", [])
    print(f"Found {len(infos)} payment infos")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admission_process_page():
    """Test fetching admission processes."""
    gql_client = get_gql_client()
    query = """
        query {
            admissionProcessPage {
                id
                paymentId
            }
        }
    """

    result = await gql_client(query, {})

    assert isinstance(result, dict)
    assert "data" in result
    processes = result["data"].get("admissionProcessPage", [])
    print(f"Found {len(processes)} processes")
