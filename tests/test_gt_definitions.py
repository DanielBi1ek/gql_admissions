import logging
import pytest

from src.GraphTypeDefinitions import schema
from src.DBFeeder import get_demodata
from .shared import prepare_demodata, prepare_in_memory_sqllite, createContext


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
                name
                programId
                paymentInfoId
            }
        }
    """
    variables = {"id": process["id"]}
    context_value = createContext(async_session_maker)

    resp = await schema.execute(query, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["id"] == process["id"]


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
                process {
                    id
                }
                enrollments {
                    id
                }
                payments {
                    id
                }
            }
        }
    """
    variables = {"id": application["id"]}
    context_value = createContext(async_session_maker)

    resp = await schema.execute(query, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["id"] == application["id"]


@pytest.mark.asyncio
async def test_payment_info_page():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    query = """
        query {
            result: paymentInfoPage {
                id
                accountNumber
            }
        }
    """
    context_value = createContext(async_session_maker)
    resp = await schema.execute(query, context_value=context_value)
    assert resp.errors is None
    assert len(resp.data["result"]) > 0


@pytest.mark.asyncio
async def test_study_program_page():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    query = """
        query {
            result: studyProgramPage {
                id
                code
            }
        }
    """
    context_value = createContext(async_session_maker)
    resp = await schema.execute(query, context_value=context_value)
    assert resp.errors is None
    assert len(resp.data["result"]) > 0
