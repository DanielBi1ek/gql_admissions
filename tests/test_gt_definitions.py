import pytest

from src.GraphTypeDefinitions import schema
from src.DBFeeder import get_demodata
from .shared import (
    prepare_demodata,
    prepare_in_memory_sqllite,
    createContext,
    execute_gql,
    uuid_to_str,
)


@pytest.mark.asyncio
async def test_admission_process_by_id():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    process = data["admission_processes"][0]

    query = """
        query($id: UUID!) {
            result: admissionProcessById(id: $id) {
                id
                paymentId
            }
        }
    """
    variables = {"id": uuid_to_str(process["id"])}
    context_value = createContext(async_session_maker)

    resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
    assert resp.data["result"]["id"] == uuid_to_str(process["id"])


@pytest.mark.asyncio
async def test_admission_application_with_relations():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    application = data["admission_applications"][0]

    query = """
        query($id: UUID!) {
            result: admissionApplicationById(id: $id) {
                id
                applicantId
                process {
                    id
                }
                payment {
                    id
                }
            }
        }
    """
    variables = {"id": uuid_to_str(application["id"])}
    context_value = createContext(async_session_maker)

    resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
    assert resp.data["result"]["id"] == uuid_to_str(application["id"])


@pytest.mark.asyncio
async def test_admission_payment_info_page():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    query = """
        query {
            result: admissionPaymentInfoPage {
                id
                bankAccountId
            }
        }
    """
    context_value = createContext(async_session_maker)
    resp = await execute_gql(schema, query, context_value=context_value)
    assert len(resp.data["result"]) > 0, f"Expected data but got empty list. Response: {resp.data}"


@pytest.mark.asyncio
async def test_admission_offer_page():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    query = """
        query {
            result: admissionOfferPage {
                id
                programId
                paymentInfoId
            }
        }
    """
    context_value = createContext(async_session_maker)
    resp = await execute_gql(schema, query, context_value=context_value)
    assert len(resp.data["result"]) > 0, f"Expected data but got empty list. Response: {resp.data}"
