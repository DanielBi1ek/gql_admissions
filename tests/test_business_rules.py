import datetime

import pytest

from src.GraphTypeDefinitions import schema
from src.DBFeeder import get_demodata
from .shared import prepare_demodata, prepare_in_memory_sqllite, createContext


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
    resp = await schema.execute(mutation, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == "b3c57cc6-4f34-4d0d-b7a8-5a47f4d58278"

    variables["input"]["applicationStartDate"] = datetime.datetime(2025, 1, 1, 10, 0, 0)
    variables["input"]["applicationEndDate"] = datetime.datetime(2025, 1, 1, 12, 0, 0)
    resp = await schema.execute(mutation, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == "c9c2f2b5-7b8b-49cf-9c73-1264f2b5353f"


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
    resp = await schema.execute(mutation, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["__typename"] == "AdmissionOfferGQLModelInsertError"
    assert resp.data["result"]["code"] == "c6f27c8c-33d8-4cd0-a76a-5eb3f4a59262"


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
    resp = await schema.execute(mutation, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["__typename"] == "AdmissionPaymentInfoGQLModelInsertError"
    assert resp.data["result"]["code"] == "f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5"


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
    offer_resp = await schema.execute(offer_create, context_value=admin_context, variable_values=variables)
    assert offer_resp.errors is None
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

    submit_resp = await schema.execute(
        submit,
        context_value=applicant_context,
        variable_values={"id": offer_id}
    )
    assert submit_resp.errors is None
    assert submit_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert submit_resp.data["result"]["code"] == "5f4c1c1d-9c2a-4c0d-9b0e-3f6f9b7d2a11"

    existing_app = None
    for app in data["admission_applications"]:
        if app.get("applicant_id") == applicant.get("id"):
            existing_app = app
            break
    assert existing_app is not None
    submit_resp = await schema.execute(
        submit,
        context_value=applicant_context,
        variable_values={"id": str(existing_app["offer_id"])}
    )
    assert submit_resp.errors is None
    assert submit_resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert submit_resp.data["result"]["code"] == "b8f0f1a1-2c3d-4e5f-8a9b-0c1d2e3f4a5b"


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
    resp = await schema.execute(mutation, context_value=context_value, variable_values=variables)
    assert resp.errors is None
    assert resp.data["result"]["__typename"] == "AdmissionApplicationGQLModelInsertError"
    assert resp.data["result"]["code"] == "a3c2a8f9-3f19-4e88-a5a0-1a7a4f6f0f8d"
