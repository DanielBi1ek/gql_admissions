import pytest

from src.GraphTypeDefinitions import schema
from src.GraphTypeDefinitions import error_codes as codes
from src.DBFeeder import get_demodata
from .shared import prepare_demodata, prepare_in_memory_sqllite, createContext, execute_gql


def _pick_applications(data):
    apps = data.get("admission_applications", [])
    if len(apps) < 2:
        raise AssertionError("Need at least two applications in demodata")
    return apps[0], apps[1]


def _pick_applicant_user_id(data, applicant_id):
    applicants = data.get("admission_applicants", [])
    for applicant in applicants:
        if applicant.get("id") == applicant_id:
            return applicant.get("applicant_user_id")
    return None


@pytest.mark.asyncio
async def test_applicant_can_withdraw_own_application():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    app, _ = _pick_applications(data)
    applicant_user_id = _pick_applicant_user_id(data, app.get("applicant_id"))
    assert applicant_user_id is not None

    mutation = """
        mutation($id: UUID!) {
            result: admissionApplicationWithdraw(withdrawal: { applicationId: $id }) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    withdrawn
                }
                ... on AdmissionApplicationGQLModelUpdateError {
                    code
                    msg
                }
            }
        }
    """
    variables = {"id": app["id"]}
    context_value = createContext(async_session_maker, user_role="none", user_id=applicant_user_id)

    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionApplicationGQLModel"
    assert resp.data["result"]["withdrawn"] is True


@pytest.mark.asyncio
async def test_applicant_cannot_withdraw_other_application():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    app, other_app = _pick_applications(data)
    applicant_user_id = _pick_applicant_user_id(data, app.get("applicant_id"))
    assert applicant_user_id is not None

    mutation = """
        mutation($id: UUID!) {
            result: admissionApplicationWithdraw(withdrawal: { applicationId: $id }) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    withdrawn
                }
                ... on AdmissionApplicationGQLModelUpdateError {
                    code
                    msg
                }
            }
        }
    """
    variables = {"id": other_app["id"]}
    context_value = createContext(async_session_maker, user_role="none", user_id=applicant_user_id)

    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelUpdateError"
    assert resp.data["result"]["code"] == codes.ERR_WITHDRAW_NOT_OWNER


@pytest.mark.asyncio
async def test_accept_blocked_for_withdrawn_application():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    app, _ = _pick_applications(data)

    update_mutation = """
        mutation($id: UUID!, $lastchange: DateTime!) {
            result: admissionApplicationUpdate(application: {
                id: $id
                lastchange: $lastchange
                withdrawn: true
            }) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    withdrawn
                }
                ... on AdmissionApplicationGQLModelUpdateError {
                    code
                    msg
                }
            }
        }
    """
    update_variables = {"id": app["id"], "lastchange": app["lastchange"]}
    admin_context = createContext(async_session_maker, user_role="administrátor")

    update_resp = await execute_gql(
        schema,
        update_mutation,
        context_value=admin_context,
        variables=update_variables,
    )
    assert update_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModel"

    accept_mutation = """
        mutation($id: UUID!) {
            result: admissionApplicationAccept(acceptance: { applicationId: $id }) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                }
                ... on AdmissionApplicationGQLModelUpdateError {
                    code
                    msg
                }
            }
        }
    """
    accept_resp = await execute_gql(
        schema,
        accept_mutation,
        context_value=admin_context,
        variables={"id": app["id"]},
    )
    assert accept_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelUpdateError"
    assert accept_resp.data["result"]["code"] == codes.ERR_APPLICATION_WITHDRAWN
