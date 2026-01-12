import datetime

import pytest

from src.GraphTypeDefinitions import schema
from src.GraphTypeDefinitions import error_codes as codes
from src.DBFeeder import get_demodata
from .shared import prepare_demodata, prepare_in_memory_sqllite, createContext, execute_gql


def _pick_program_without_offer(data):
    offers = data.get("admission_offers", [])
    offered_programs = {offer.get("program_id") for offer in offers}
    programs = data.get("study_programs", [])
    for program in programs:
        if program.get("id") not in offered_programs:
            return program
    return None


@pytest.mark.asyncio
async def test_offer_create_date_validation():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    program = _pick_program_without_offer(data)
    assert program is not None
    payment_info_id = data["admission_payment_infos"][0]["id"]
    context_value = createContext(async_session_maker, user_role="administrátor")

    mutation = """
        mutation($input: AdmissionOfferCreateGQLModel!) {
            result: admissionOfferCreate(admissionOffer: $input) {
                __typename
                ... on AdmissionOfferGQLModel { id }
                ... on AdmissionOfferGQLModelInsertError { code msg }
            }
        }
    """

    variables = {
        "input": {
            "programId": str(program["id"]),
            "applicationStartDate": datetime.datetime(2025, 1, 2, 10, 0, 0),
            "applicationEndDate": datetime.datetime(2025, 1, 1, 10, 0, 0),
            "paymentInfoId": str(payment_info_id),
        }
    }
    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == codes.ERR_OFFER_END_BEFORE_START

    variables["input"]["applicationStartDate"] = datetime.datetime(2025, 1, 1, 10, 0, 0)
    variables["input"]["applicationEndDate"] = datetime.datetime(2025, 1, 1, 12, 0, 0)
    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == codes.ERR_OFFER_SAME_DAY


@pytest.mark.asyncio
async def test_offer_create_duplicate_program():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    offer = data["admission_offers"][0]
    payment_info_id = data["admission_payment_infos"][0]["id"]
    context_value = createContext(async_session_maker, user_role="administrátor")

    mutation = """
        mutation($input: AdmissionOfferCreateGQLModel!) {
            result: admissionOfferCreate(admissionOffer: $input) {
                __typename
                ... on AdmissionOfferGQLModel { id }
                ... on AdmissionOfferGQLModelInsertError { code msg }
            }
        }
    """

    variables = {
        "input": {
            "programId": str(offer["program_id"]),
            "applicationStartDate": datetime.datetime(2025, 1, 1, 10, 0, 0),
            "applicationEndDate": datetime.datetime(2025, 1, 2, 10, 0, 0),
            "paymentInfoId": str(payment_info_id),
        }
    }
    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == codes.ERR_OFFER_EXISTS


@pytest.mark.asyncio
async def test_payment_info_required_amount_validation():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    bank_account_id = data["admission_bank_accounts"][0]["id"]
    context_value = createContext(async_session_maker, user_role="administrátor")

    mutation = """
        mutation($input: AdmissionPaymentInfoCreateGQLModel!) {
            result: admissionPaymentInfoCreate(paymentInfo: $input) {
                __typename
                ... on AdmissionPaymentInfoGQLModel { id }
                ... on AdmissionPaymentInfoGQLModelInsertError { code msg }
            }
        }
    """

    variables = {
        "input": {
            "requiredAmount": 0,
            "bankAccountId": str(bank_account_id),
        }
    }
    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionPaymentInfoGQLModelInsertError"
    assert resp.data["result"]["code"] == codes.ERR_REQUIRED_POSITIVE


@pytest.mark.asyncio
async def test_application_submit_date_window_and_duplicate():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    program = _pick_program_without_offer(data)
    payment_info_id = data["admission_payment_infos"][0]["id"]
    applicant = data["admission_applicants"][0]

    admin_context = createContext(async_session_maker, user_role="administrátor")
    applicant_context = createContext(
        async_session_maker,
        user_role="none",
        user_id=applicant["applicant_user_id"],
    )

    offer_create = """
        mutation($input: AdmissionOfferCreateGQLModel!) {
            result: admissionOfferCreate(admissionOffer: $input) {
                __typename
                ... on AdmissionOfferGQLModel { id }
                ... on AdmissionOfferGQLModelInsertError { code msg }
            }
        }
    """

    now = datetime.datetime.now()
    variables = {
        "input": {
            "programId": str(program["id"]),
            "applicationStartDate": now + datetime.timedelta(days=10),
            "applicationEndDate": now + datetime.timedelta(days=11),
            "paymentInfoId": str(payment_info_id),
        }
    }
    offer_resp = await execute_gql(
        schema,
        offer_create,
        context_value=admin_context,
        variables=variables,
    )
    offer_id = offer_resp.data["result"]["id"]

    submit = """
        mutation($id: UUID!) {
            result: admissionApplicationSubmit(submission: { offerId: $id }) {
                __typename
                ... on AdmissionApplicationGQLModel { id }
                ... on AdmissionApplicationGQLModelInsertError { code msg }
            }
        }
    """

    submit_resp = await execute_gql(
        schema,
        submit,
        context_value=applicant_context,
        variables={"id": offer_id},
    )
    assert submit_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert submit_resp.data["result"]["code"] == codes.ERR_OFFER_NOT_STARTED

    existing_app = None
    for app in data["admission_applications"]:
        if app.get("applicant_id") == applicant.get("id"):
            existing_app = app
            break
    assert existing_app is not None
    submit_resp = await execute_gql(
        schema,
        submit,
        context_value=applicant_context,
        variables={"id": str(existing_app["offer_id"])},
    )
    assert submit_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert submit_resp.data["result"]["code"] == codes.ERR_APPLICATION_EXISTS


@pytest.mark.asyncio
async def test_application_insert_missing_required_fields():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    application = data["admission_applications"][0]
    context_value = createContext(async_session_maker, user_role="administrátor")

    mutation = """
        mutation($input: AdmissionApplicationInsertGQLModel!) {
            result: admissionApplicationInsert(application: $input) {
                __typename
                ... on AdmissionApplicationGQLModel { id }
                ... on AdmissionApplicationGQLModelInsertError { code msg }
            }
        }
    """

    variables = {
        "input": {
            "applicantId": str(application["applicant_id"]),
            "offerId": str(application["offer_id"]),
            "paymentId": None,
        }
    }
    resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
    assert resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert resp.data["result"]["code"] == codes.ERR_MISSING_REQUIRED
