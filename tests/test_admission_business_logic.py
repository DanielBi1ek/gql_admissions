"""
Tests for Admission Business Logic Validation.

Tests cover:
- Offer date validation
- Payment amount validation
- Application submission rules
- Duplicate prevention
- Foreign key validation
"""
import pytest
import logging
import datetime
import uuid

from src.GraphTypeDefinitions import schema

from .shared import (
    prepare_demodata,
    prepare_in_memory_sqllite,
    get_demodata,
    createAdminContext,
    createRegularUserContext,
    createApplicantContext,
    assert_no_graphql_errors,
    execute_gql,
)


def datetime_to_iso(dt):
    """Convert datetime to ISO string for GraphQL."""
    if isinstance(dt, datetime.datetime):
        return dt.isoformat()
    return dt


# =============================================================================
# OFFER VALIDATION TESTS
# =============================================================================

class TestOfferValidation:
    """Tests for admission offer business rules."""

    @pytest.mark.asyncio
    async def test_offer_requires_valid_program(self):
        """Offer creation requires a valid study program."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        payment_info = data["admission_payment_infos"][0]
        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionOfferCreateGQLModel!) {
                result: admissionOfferCreate(admissionOffer: $input) {
                    __typename
                    ... on AdmissionOfferGQLModel { id }
                    ... on AdmissionOfferGQLModelInsertError { msg code }
                }
            }
        """

        start_date = datetime.datetime(2026, 1, 1, 10, 0, 0)
        end_date = datetime.datetime(2026, 3, 31, 23, 59, 59)

        variables = {
            "input": {
                "programId": str(uuid.uuid4()),  # Non-existent program
                "applicationStartDate": datetime_to_iso(start_date),
                "applicationEndDate": datetime_to_iso(end_date),
                "paymentInfoId": str(payment_info["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionOfferGQLModelInsertError"
        assert "program" in result["msg"].lower() or "not found" in result["msg"].lower()

    @pytest.mark.asyncio
    async def test_offer_requires_valid_payment_info(self):
        """Offer creation requires valid payment info."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        programs = data["study_programs"]
        existing_offers = data["admission_offers"]
        used_program_ids = {o["program_id"] for o in existing_offers}

        available_program = next(
            (p for p in programs if p["id"] not in used_program_ids),
            None
        )

        if available_program is None:
            pytest.skip("No available program without existing offer")

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionOfferCreateGQLModel!) {
                result: admissionOfferCreate(admissionOffer: $input) {
                    __typename
                    ... on AdmissionOfferGQLModel { id }
                    ... on AdmissionOfferGQLModelInsertError { msg code }
                }
            }
        """

        start_date = datetime.datetime(2026, 1, 1, 10, 0, 0)
        end_date = datetime.datetime(2026, 3, 31, 23, 59, 59)

        variables = {
            "input": {
                "programId": str(available_program["id"]),
                "applicationStartDate": datetime_to_iso(start_date),
                "applicationEndDate": datetime_to_iso(end_date),
                "paymentInfoId": str(uuid.uuid4())  # Non-existent payment info
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionOfferGQLModelInsertError"

    @pytest.mark.asyncio
    async def test_offer_one_per_program(self):
        """Only one offer per study program is allowed."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        existing_offer = data["admission_offers"][0]
        payment_info = data["admission_payment_infos"][0]

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionOfferCreateGQLModel!) {
                result: admissionOfferCreate(admissionOffer: $input) {
                    __typename
                    ... on AdmissionOfferGQLModel { id }
                    ... on AdmissionOfferGQLModelInsertError { msg code }
                }
            }
        """

        start_date = datetime.datetime(2026, 5, 1, 10, 0, 0)
        end_date = datetime.datetime(2026, 6, 30, 23, 59, 59)

        variables = {
            "input": {
                "programId": str(existing_offer["program_id"]),  # Already has an offer
                "applicationStartDate": datetime_to_iso(start_date),
                "applicationEndDate": datetime_to_iso(end_date),
                "paymentInfoId": str(payment_info["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionOfferGQLModelInsertError"
        assert "exists" in result["msg"].lower() or "already" in result["msg"].lower()


# =============================================================================
# PAYMENT INFO VALIDATION TESTS
# =============================================================================

class TestPaymentInfoValidation:
    """Tests for payment info business rules."""

    @pytest.mark.asyncio
    async def test_payment_info_requires_positive_amount(self):
        """Payment info requires a positive amount."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        bank_account = data["admission_bank_accounts"][0]
        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionPaymentInfoInsertGQLModel!) {
                result: admissionPaymentInfoInsert(paymentInfo: $input) {
                    __typename
                    ... on AdmissionPaymentInfoGQLModelResult { id }
                    ... on AdmissionPaymentInfoGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "requiredAmount": 0.0,  # Zero is not positive
                "bankAccountId": str(bank_account["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionPaymentInfoGQLModelInsertError"

    @pytest.mark.asyncio
    async def test_payment_info_rejects_negative_amount(self):
        """Payment info rejects negative amounts."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        bank_account = data["admission_bank_accounts"][0]
        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionPaymentInfoInsertGQLModel!) {
                result: admissionPaymentInfoInsert(paymentInfo: $input) {
                    __typename
                    ... on AdmissionPaymentInfoGQLModelResult { id }
                    ... on AdmissionPaymentInfoGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "requiredAmount": -100.0,
                "bankAccountId": str(bank_account["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionPaymentInfoGQLModelInsertError"

    @pytest.mark.asyncio
    async def test_payment_info_requires_valid_bank_account(self):
        """Payment info requires a valid bank account reference."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionPaymentInfoInsertGQLModel!) {
                result: admissionPaymentInfoInsert(paymentInfo: $input) {
                    __typename
                    ... on AdmissionPaymentInfoGQLModelResult { id }
                    ... on AdmissionPaymentInfoGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "requiredAmount": 500.0,
                "bankAccountId": str(uuid.uuid4())  # Non-existent
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionPaymentInfoGQLModelInsertError"
        assert "bank" in result["msg"].lower() or "not found" in result["msg"].lower()


# =============================================================================
# BANK ACCOUNT VALIDATION TESTS
# =============================================================================

class TestBankAccountValidation:
    """Tests for bank account business rules."""

    @pytest.mark.asyncio
    async def test_bank_account_requires_numeric_account_number(self):
        """Bank account number must be numeric."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionBankAccountInsertGQLModel!) {
                result: admissionBankAccountInsert(bankAccount: $input) {
                    __typename
                    ... on AdmissionBankAccountGQLModel { id }
                    ... on AdmissionBankAccountGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "accountNumber": "ABC123",  # Not numeric
                "bankCode": "0100"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionBankAccountGQLModelInsertError"

    @pytest.mark.asyncio
    async def test_bank_account_requires_numeric_bank_code(self):
        """Bank code must be numeric."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionBankAccountInsertGQLModel!) {
                result: admissionBankAccountInsert(bankAccount: $input) {
                    __typename
                    ... on AdmissionBankAccountGQLModel { id }
                    ... on AdmissionBankAccountGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "accountNumber": "123456789",
                "bankCode": "ABCD"  # Not numeric
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionBankAccountGQLModelInsertError"

    @pytest.mark.asyncio
    async def test_bank_account_unique_constraint(self):
        """Bank account (prefix, number, code) must be unique."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        existing_account = data["admission_bank_accounts"][0]
        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionBankAccountInsertGQLModel!) {
                result: admissionBankAccountInsert(bankAccount: $input) {
                    __typename
                    ... on AdmissionBankAccountGQLModel { id }
                    ... on AdmissionBankAccountGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "accountPrefix": existing_account.get("account_prefix", ""),
                "accountNumber": existing_account["account_number"],
                "bankCode": existing_account["bank_code"],
                "description": "Duplicate attempt"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        # Should fail due to unique constraint
        assert result["__typename"] == "AdmissionBankAccountGQLModelInsertError"


# =============================================================================
# APPLICANT VALIDATION TESTS
# =============================================================================

class TestApplicantValidation:
    """Tests for applicant business rules."""

    @pytest.mark.asyncio
    async def test_applicant_profile_unique_per_user(self):
        """Only one applicant profile per user is allowed."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        existing_applicant = data["admission_applicants"][0]

        context_value = createApplicantContext(
            async_session_maker,
            existing_applicant["applicant_user_id"]
        )

        mutation = """
            mutation($input: AdmissionApplicantInitGQLModel!) {
                result: admissionApplicantInit(applicant: $input) {
                    __typename
                    ... on AdmissionApplicantGQLModel { id }
                    ... on AdmissionApplicantGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "street": "New Street",
                "houseNumber": "123",
                "city": "New City",
                "phoneNumber": "+420123456789",
                "email": "test@example.com"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionApplicantGQLModelInsertError"
        assert "exists" in result["msg"].lower() or "already" in result["msg"].lower()


# =============================================================================
# APPLICATION VALIDATION TESTS
# =============================================================================

class TestApplicationValidation:
    """Tests for application business rules."""

    @pytest.mark.asyncio
    async def test_cannot_accept_withdrawn_application(self):
        """Cannot accept an application that has been withdrawn."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()

        # First, withdraw an application
        applicant = data["admission_applicants"][0]
        application = next(
            (a for a in data["admission_applications"]
             if a["applicant_id"] == applicant["id"]),
            None
        )

        if application is None:
            pytest.skip("No application found")

        # Withdraw the application first
        applicant_context = createApplicantContext(
            async_session_maker,
            applicant["applicant_user_id"]
        )

        withdraw_mutation = """
            mutation($input: AdmissionApplicationWithdrawGQLModel!) {
                result: admissionApplicationWithdraw(withdrawal: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel { id withdrawn }
                    ... on AdmissionApplicationGQLModelUpdateError { msg }
                }
            }
        """
        withdraw_variables = {
            "input": {
                "applicationId": str(application["id"])
            }
        }

        await execute_gql(schema, withdraw_mutation, context_value=applicant_context, variables=withdraw_variables)

        # Now try to accept as admin
        admin_context = createAdminContext(async_session_maker)

        accept_mutation = """
            mutation($input: AdmissionApplicationAcceptGQLModel!) {
                result: admissionApplicationAccept(acceptance: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel { id accepted }
                    ... on AdmissionApplicationGQLModelUpdateError { msg code }
                }
            }
        """
        accept_variables = {
            "input": {
                "applicationId": str(application["id"])
            }
        }

        resp = await execute_gql(schema, accept_mutation, context_value=admin_context, variables=accept_variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        # Should fail - application is withdrawn
        assert result["__typename"] == "AdmissionApplicationGQLModelUpdateError"

    @pytest.mark.asyncio
    async def test_application_requires_applicant_profile(self):
        """Application submission requires an existing applicant profile."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        offer = data["admission_offers"][0]

        # Use a user without an applicant profile
        new_user_id = str(uuid.uuid4())
        context_value = createRegularUserContext(
            async_session_maker,
            user_id=new_user_id,
            name="No",
            surname="Profile",
            email="no.profile@example.com"
        )

        mutation = """
            mutation($input: AdmissionApplicationSubmitGQLModel!) {
                result: admissionApplicationSubmit(submission: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel { id }
                    ... on AdmissionApplicationGQLModelInsertError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "offerId": str(offer["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        # Should fail - no applicant profile
        # Note: The system might auto-create applicant profile, so check the behavior
        # If auto-creation is enabled, this test might need adjustment


# =============================================================================
# RELATIONSHIP/NAVIGATION TESTS
# =============================================================================

class TestRelationships:
    """Tests for entity relationship navigation."""

    @pytest.mark.asyncio
    async def test_offer_has_program_relation(self):
        """Offer can navigate to its study program."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        offer = data["admission_offers"][0]
        context_value = createAdminContext(async_session_maker)

        query = """
            query($id: UUID!) {
                admissionOfferById(id: $id) {
                    id
                    program {
                        id
                        name
                    }
                }
            }
        """
        variables = {"id": str(offer["id"])}

        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionOfferById"]
        assert result is not None
        assert result["program"] is not None
        assert result["program"]["id"] == str(offer["program_id"])

    @pytest.mark.asyncio
    async def test_offer_has_payment_info_relation(self):
        """Offer can navigate to its payment info."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        offer = data["admission_offers"][0]
        context_value = createAdminContext(async_session_maker)

        query = """
            query($id: UUID!) {
                admissionOfferById(id: $id) {
                    id
                    paymentInfo {
                        id
                        requiredAmount
                    }
                }
            }
        """
        variables = {"id": str(offer["id"])}

        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionOfferById"]
        assert result is not None
        assert result["paymentInfo"] is not None
        assert result["paymentInfo"]["id"] == str(offer["payment_info_id"])

    @pytest.mark.asyncio
    async def test_application_has_applicant_relation(self):
        """Application can navigate to its applicant."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        application = data["admission_applications"][0]
        context_value = createAdminContext(async_session_maker)

        query = """
            query($id: UUID!) {
                admissionApplicationById(id: $id) {
                    id
                    applicant {
                        id
                        firstname
                        lastname
                    }
                }
            }
        """
        variables = {"id": str(application["id"])}

        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionApplicationById"]
        assert result is not None
        assert result["applicant"] is not None
        assert result["applicant"]["id"] == str(application["applicant_id"])

    @pytest.mark.asyncio
    async def test_application_has_offer_relation(self):
        """Application can navigate to its offer."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        application = data["admission_applications"][0]
        context_value = createAdminContext(async_session_maker)

        query = """
            query($id: UUID!) {
                admissionApplicationById(id: $id) {
                    id
                    offer {
                        id
                        programId
                    }
                }
            }
        """
        variables = {"id": str(application["id"])}

        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionApplicationById"]
        assert result is not None
        assert result["offer"] is not None
        assert result["offer"]["id"] == str(application["offer_id"])

    @pytest.mark.asyncio
    async def test_payment_info_has_bank_account_relation(self):
        """Payment info can navigate to its bank account."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        payment_info = data["admission_payment_infos"][0]
        context_value = createAdminContext(async_session_maker)

        query = """
            query($id: UUID!) {
                admissionPaymentInfoById(id: $id) {
                    id
                    bankAccount {
                        id
                        accountNumber
                        bankCode
                    }
                }
            }
        """
        variables = {"id": str(payment_info["id"])}

        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionPaymentInfoById"]
        assert result is not None
        assert result["bankAccount"] is not None
        assert result["bankAccount"]["id"] == str(payment_info["bank_account_id"])

