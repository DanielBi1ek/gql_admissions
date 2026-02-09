"""
Tests for Admission RBAC (Role-Based Access Control).

Tests cover:
- Admin vs regular user permissions
- Unauthenticated access denial
- Owner-only access for applicants and applications
- Permission boundaries for all operations
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
    is_federation_mode,
    createContext,
    createAdminContext,
    createRegularUserContext,
    createApplicantContext,
    createUnauthenticatedContext,
    assert_no_graphql_errors,
    execute_gql,
    generate_uuid,
)


def datetime_to_iso(dt):
    """Convert datetime to ISO string for GraphQL."""
    if isinstance(dt, datetime.datetime):
        return dt.isoformat()
    return dt


def _random_digits(length=9):
    """Return a digit-only string suitable for unique bank identifiers."""
    digits = ''.join(filter(str.isdigit, uuid.uuid4().hex))
    while len(digits) < length:
        digits += ''.join(filter(str.isdigit, uuid.uuid4().hex))
    return digits[:length]


# =============================================================================
# UNAUTHENTICATED ACCESS TESTS
# =============================================================================

class TestUnauthenticatedAccess:
    """Tests verifying unauthenticated users are denied access."""

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_query_offers(self):
        """Unauthenticated users cannot query admission offers."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createUnauthenticatedContext(async_session_maker)

        query = """
            query {
                admissionOfferPage {
                    id
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        # Should either have errors or return null/empty
        has_permission_error = resp.errors is not None
        has_empty_result = resp.data is None or resp.data.get("admissionOfferPage") is None
        assert has_permission_error or has_empty_result

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_query_applicants(self):
        """Unauthenticated users cannot query applicants."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createUnauthenticatedContext(async_session_maker)

        query = """
            query {
                admissionApplicantPage {
                    id
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        has_permission_error = resp.errors is not None
        has_empty_result = resp.data is None or resp.data.get("admissionApplicantPage") == []
        assert has_permission_error or has_empty_result

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_query_applications(self):
        """Unauthenticated users cannot query applications."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createUnauthenticatedContext(async_session_maker)

        query = """
            query {
                admissionApplicationPage {
                    id
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        has_permission_error = resp.errors is not None
        has_empty_result = resp.data is None or resp.data.get("admissionApplicationPage") == []
        assert has_permission_error or has_empty_result


# =============================================================================
# ADMIN PERMISSION TESTS
# =============================================================================

class TestAdminPermissions:
    """Tests verifying admin-only operations."""

    @pytest.mark.asyncio
    async def test_admin_can_view_all_applicants(self):
        """Admin can view all applicants."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        context_value = createAdminContext(async_session_maker)

        query = """
            query {
                admissionApplicantPage(limit: 100) {
                    id
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionApplicantPage"]
        assert len(result) == len(data["admission_applicants"])

    @pytest.mark.asyncio
    async def test_admin_can_view_all_applications(self):
        """Admin can view all applications."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        context_value = createAdminContext(async_session_maker)

        query = """
            query {
                admissionApplicationPage(limit: 100) {
                    id
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionApplicationPage"]
        if is_federation_mode():
            # Live federation DB can contain more rows than the local seed.
            assert len(result) >= len(data["admission_applications"])
        else:
            assert len(result) == len(data["admission_applications"])

    @pytest.mark.asyncio
    async def test_admin_can_insert_bank_account(self):
        """Admin can insert bank accounts."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createAdminContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionBankAccountInsertGQLModel!) {
                result: admissionBankAccountInsert(bankAccount: $input) {
                    __typename
                    ... on AdmissionBankAccountGQLModel { id }
                    ... on AdmissionBankAccountGQLModelInsertError { msg }
                }
            }
        """
        variables = {
            "input": {
                "accountPrefix": _random_digits(3),
                "accountNumber": _random_digits(9),
                "bankCode": _random_digits(4),
                "description": "Admin created account"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionBankAccountGQLModel", result

    @pytest.mark.asyncio
    async def test_admin_can_accept_application(self):
        """Admin can accept applications."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createAdminContext(async_session_maker)
        if is_federation_mode():
            # Find a pending application in the live API.
            page_query = """
                query {
                    admissionApplicationPage(limit: 100) {
                        id
                        accepted
                        withdrawn
                    }
                }
            """
            page = await execute_gql(schema, page_query, context_value=context_value)
            assert_no_graphql_errors(page)
            apps = page.data.get("admissionApplicationPage") or []
            application_id = next(
                (a["id"] for a in apps if not a.get("accepted") and not a.get("withdrawn")),
                None,
            )
            if application_id is None:
                pytest.skip("No pending application found in federation environment")
        else:
            data = get_demodata()
            application = next(
                (a for a in data["admission_applications"]
                 if not a.get("accepted") and not a.get("withdrawn")),
                None
            )
            if application is None:
                pytest.skip("No pending application found")
            application_id = str(application["id"])

        mutation = """
            mutation($input: AdmissionApplicationAcceptGQLModel!) {
                result: admissionApplicationAccept(acceptance: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel {
                        id
                        accepted
                    }
                    ... on AdmissionApplicationGQLModelUpdateError { msg }
                }
            }
        """
        variables = {
            "input": {
                "applicationId": application_id
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        if result["__typename"] == "AdmissionApplicationGQLModel":
            assert result["accepted"] is True
        else:
            # Can happen on re-run if it got accepted between page+mutation.
            assert result["__typename"] == "AdmissionApplicationGQLModelUpdateError"
            assert "accepted" in (result.get("msg") or "").lower()


# =============================================================================
# REGULAR USER PERMISSION TESTS
# =============================================================================

class TestRegularUserPermissions:
    """Tests verifying regular user restrictions."""

    @pytest.mark.asyncio
    async def test_regular_user_cannot_insert_bank_account(self):
        """Regular user cannot insert bank accounts."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createRegularUserContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionBankAccountInsertGQLModel!) {
                result: admissionBankAccountInsert(bankAccount: $input) {
                    __typename
                    ... on AdmissionBankAccountGQLModel { id }
                    ... on AdmissionBankAccountGQLModelInsertError { msg }
                }
            }
        """
        variables = {
            "input": {
                "accountNumber": "123456789",
                "bankCode": "0100"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        # Should have permission error
        assert resp.errors is not None or resp.data.get("result") is None

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_offer(self):
        """Regular user cannot create offers."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        payment_info = data["admission_payment_infos"][0]
        programs = data["study_programs"]

        context_value = createRegularUserContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionOfferCreateGQLModel!) {
                result: admissionOfferCreate(admissionOffer: $input) {
                    __typename
                    ... on AdmissionOfferGQLModel { id }
                    ... on AdmissionOfferGQLModelInsertError { msg }
                }
            }
        """

        start_date = datetime.datetime(2026, 5, 1, 10, 0, 0)
        end_date = datetime.datetime(2026, 6, 30, 23, 59, 59)

        variables = {
            "input": {
                "programId": str(programs[0]["id"]),
                "applicationStartDate": datetime_to_iso(start_date),
                "applicationEndDate": datetime_to_iso(end_date),
                "paymentInfoId": str(payment_info["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        # Should have permission error
        assert resp.errors is not None or resp.data.get("result") is None

    @pytest.mark.asyncio
    async def test_regular_user_cannot_accept_application(self):
        """Regular user cannot accept applications."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        data = get_demodata()
        application = data["admission_applications"][0]

        context_value = createRegularUserContext(async_session_maker)

        mutation = """
            mutation($input: AdmissionApplicationAcceptGQLModel!) {
                result: admissionApplicationAccept(acceptance: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel { id }
                    ... on AdmissionApplicationGQLModelUpdateError { msg }
                }
            }
        """
        variables = {
            "input": {
                "applicationId": str(application["id"])
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        # Should have permission error
        assert resp.errors is not None or resp.data.get("result") is None


# =============================================================================
# OWNER-BASED ACCESS CONTROL TESTS
# =============================================================================

class TestOwnerBasedAccess:
    """Tests verifying owner-only access for personal data."""

    @pytest.mark.asyncio
    async def test_applicant_can_only_see_own_profile(self):
        """Applicant can only see their own profile in page query."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = (
            createRegularUserContext(async_session_maker)
            if is_federation_mode()
            else createApplicantContext(async_session_maker, get_demodata()["admission_applicants"][0]["applicant_user_id"])
        )

        query = """
            query {
                me { id }
                admissionApplicantPage {
                    id
                    applicantUserId
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        assert_no_graphql_errors(resp)

        me_id = resp.data.get("me", {}).get("id")
        result = resp.data["admissionApplicantPage"] or []
        assert len(result) <= 1
        if me_id and result:
            assert all(row.get("applicantUserId") == me_id for row in result)

    @pytest.mark.asyncio
    async def test_applicant_cannot_see_other_profiles(self):
        """Applicant cannot see other applicants' profiles by ID."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        if is_federation_mode():
            admin_ctx = createAdminContext(async_session_maker)
            admin_query = """
                query {
                    admissionApplicantPage(limit: 100) { id applicantUserId }
                }
            """
            admin_resp = await execute_gql(schema, admin_query, context_value=admin_ctx)
            assert_no_graphql_errors(admin_resp)
            candidates = admin_resp.data.get("admissionApplicantPage") or []

            context_value = createRegularUserContext(async_session_maker)
            me_resp = await execute_gql(schema, "query{ me { id } }", context_value=context_value)
            assert_no_graphql_errors(me_resp)
            me_id = me_resp.data.get("me", {}).get("id")
            other_id = next((r["id"] for r in candidates if me_id and r.get("applicantUserId") != me_id), None)
            if other_id is None:
                pytest.skip("No other applicant found to test access denial")
            variables = {"id": other_id}
        else:
            data = get_demodata()
            applicant1 = data["admission_applicants"][0]
            applicant2 = data["admission_applicants"][1]
            context_value = createApplicantContext(async_session_maker, applicant1["applicant_user_id"])
            variables = {"id": str(applicant2["id"])}

        query = """
            query($id: UUID!) {
                admissionApplicantById(id: $id) {
                    id
                    firstname
                }
            }
        """
        resp = await execute_gql(schema, query, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        # Should return null - no access to other's profile
        result = resp.data["admissionApplicantById"]
        assert result is None

    @pytest.mark.asyncio
    async def test_applicant_can_withdraw_own_application(self):
        """Applicant can withdraw their own application."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = (
            createRegularUserContext(async_session_maker)
            if is_federation_mode()
            else createApplicantContext(async_session_maker, get_demodata()["admission_applicants"][0]["applicant_user_id"])
        )
        if is_federation_mode():
            page_query = """
                query {
                    admissionApplicationPage(limit: 100) { id withdrawn }
                }
            """
            page = await execute_gql(schema, page_query, context_value=context_value)
            assert_no_graphql_errors(page)
            apps = page.data.get("admissionApplicationPage") or []
            app_id = next((a["id"] for a in apps if not a.get("withdrawn")), None)
            if app_id is None:
                pytest.skip("No non-withdrawn application found for current user")
        else:
            data = get_demodata()
            applicant = data["admission_applicants"][0]
            applicant_user_id = applicant["applicant_user_id"]
            own_application = next(
                (a for a in data["admission_applications"]
                 if a["applicant_id"] == applicant["id"]),
                None
            )
            if own_application is None:
                pytest.skip("No application found for applicant")
            context_value = createApplicantContext(async_session_maker, applicant_user_id)
            app_id = str(own_application["id"])

        mutation = """
            mutation($input: AdmissionApplicationWithdrawGQLModel!) {
                result: admissionApplicationWithdraw(withdrawal: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel {
                        id
                        withdrawn
                    }
                    ... on AdmissionApplicationGQLModelUpdateError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "applicationId": app_id
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionApplicationGQLModel"
        assert result["withdrawn"] == True

    @pytest.mark.asyncio
    async def test_applicant_cannot_withdraw_other_application(self):
        """Applicant cannot withdraw another applicant's application."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        if is_federation_mode():
            admin_ctx = createAdminContext(async_session_maker)
            admin_query = """
                query {
                    admissionApplicationPage(limit: 100) { id applicantId }
                    admissionApplicantPage(limit: 100) { id applicantUserId }
                }
            """
            admin_resp = await execute_gql(schema, admin_query, context_value=admin_ctx)
            assert_no_graphql_errors(admin_resp)
            apps = admin_resp.data.get("admissionApplicationPage") or []
            applicants = admin_resp.data.get("admissionApplicantPage") or []
            applicant_to_user = {a["id"]: a.get("applicantUserId") for a in applicants}

            context_value = createRegularUserContext(async_session_maker)
            me_resp = await execute_gql(schema, "query{ me { id } }", context_value=context_value)
            assert_no_graphql_errors(me_resp)
            me_id = me_resp.data.get("me", {}).get("id")

            other_app_id = next(
                (a["id"] for a in apps if me_id and applicant_to_user.get(a.get("applicantId")) != me_id),
                None,
            )
            if other_app_id is None:
                pytest.skip("No other application found to test withdraw denial")
            target_id = other_app_id
        else:
            data = get_demodata()
            applicant1 = data["admission_applicants"][0]
            applicant2 = data["admission_applicants"][1]
            other_application = next(
                (a for a in data["admission_applications"]
                 if a["applicant_id"] == applicant2["id"]),
                None
            )
            if other_application is None:
                pytest.skip("No application found for applicant2")
            context_value = createApplicantContext(async_session_maker, applicant1["applicant_user_id"])
            target_id = str(other_application["id"])

        mutation = """
            mutation($input: AdmissionApplicationWithdrawGQLModel!) {
                result: admissionApplicationWithdraw(withdrawal: $input) {
                    __typename
                    ... on AdmissionApplicationGQLModel { id }
                    ... on AdmissionApplicationGQLModelUpdateError { msg code }
                }
            }
        """
        variables = {
            "input": {
                "applicationId": target_id
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        # Should return an error - not owner
        assert result["__typename"] == "AdmissionApplicationGQLModelUpdateError"


# =============================================================================
# AUTHENTICATED USER CAN ACCESS PUBLIC DATA TESTS
# =============================================================================

class TestAuthenticatedPublicAccess:
    """Tests verifying authenticated users can access public data."""

    @pytest.mark.asyncio
    async def test_authenticated_user_can_view_offers(self):
        """Any authenticated user can view admission offers."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createRegularUserContext(async_session_maker)

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

        resp = await execute_gql(schema, query, context_value=context_value)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionOfferPage"]
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_authenticated_user_can_view_bank_accounts(self):
        """Any authenticated user can view bank accounts."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        context_value = createRegularUserContext(async_session_maker)

        query = """
            query {
                admissionBankAccountPage {
                    id
                    accountNumber
                    bankCode
                }
            }
        """

        resp = await execute_gql(schema, query, context_value=context_value)
        assert_no_graphql_errors(resp)

        result = resp.data["admissionBankAccountPage"]
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_authenticated_user_can_init_applicant(self):
        """Any authenticated user can initialize their applicant profile."""
        async_session_maker = await prepare_in_memory_sqllite()
        await prepare_demodata(async_session_maker)

        if is_federation_mode():
            pytest.skip("Cannot create a brand-new user in federation mode without seeding OAuth/UG")

        # Use a new user ID that doesn't have a profile
        new_user_id = str(uuid.uuid4())
        context_value = createRegularUserContext(
            async_session_maker,
            user_id=new_user_id,
            name="New",
            surname="User",
            email="new.user@example.com"
        )

        mutation = """
            mutation($input: AdmissionApplicantInitGQLModel!) {
                result: admissionApplicantInit(applicant: $input) {
                    __typename
                    ... on AdmissionApplicantGQLModel {
                        id
                        firstname
                        lastname
                    }
                    ... on AdmissionApplicantGQLModelInsertError { msg }
                }
            }
        """
        variables = {
            "input": {
                "street": "New Street",
                "houseNumber": "999",
                "city": "New City",
                "phoneNumber": "+420555666777",
                "email": "new.user@example.com"
            }
        }

        resp = await execute_gql(schema, mutation, context_value=context_value, variables=variables)
        assert_no_graphql_errors(resp)

        result = resp.data["result"]
        assert result["__typename"] == "AdmissionApplicantGQLModel"
        assert result["firstname"] == "New"
        assert result["lastname"] == "User"
