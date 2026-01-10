"""
Tests for RBAC (Role-Based Access Control) on Admission Applications

Tests cover:
1. Users with editor role can create admission applications
2. Users without required roles cannot create admission applications
3. Creators can update/delete their own applications (creator ownership)
4. Users with admin roles can delete applications
5. Users with editor roles in the same group can update applications
6. Users without proper roles cannot update/delete applications

Uses real users from systemdata.json with proper role structures.
"""

import logging
import pytest
import uuid
import datetime

from src.GraphTypeDefinitions import schema
from src.DBFeeder import get_demodata
from .shared import prepare_demodata, prepare_in_memory_sqllite, createContext


def _uuid_to_str(val):
    """Convert UUID object to string if needed"""
    if isinstance(val, uuid.UUID):
        return str(val)
    return val


# ===========================================================================================
# TEST FIXTURES - Real users from systemdata.json
# ===========================================================================================

def create_user_context(async_session_maker, user_email, user_id, fullname, roles):
    """Create a context with a real user structure matching what comes from UG service"""
    context = createContext(async_session_maker, withuser=False)
    context["user"] = {
        "id": user_id,
        "email": user_email,
        "fullname": fullname,
        "roles": roles
    }
    return context


def get_john_newbie_context(async_session_maker):
    """John Newbie - has 'administrátor' role in Univerzita group"""
    return create_user_context(
        async_session_maker,
        user_email="john.newbie@world.com",
        user_id="2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
        fullname="John Newbie",
        roles=[
            {
                "id": "77777777-0001-4000-8000-000000000001",
                "roletype": {"name": "administrátor"},
                "roletypeId": "ed1707aa-0000-4000-8000-000000000001",
                "group": {
                    "id": "f2f2d33c-38ee-4f31-9426-f364bc488032",  # Univerzita
                    "name": "Univerzita obrany",
                    "grouptype": {"name": "univerzita"}
                }
            }
        ]
    )


def get_oliver_hortik_context(async_session_maker):
    """Oliver Hortík - has 'viewer' and 'odpovědný řešitel' roles"""
    return create_user_context(
        async_session_maker,
        user_email="Oliver.Hortik@world.com",
        user_id="6a6ca6e9-2222-498f-b270-b7b07c2afa41",
        fullname="Oliver Hortík",
        roles=[
            {
                "id": "77777777-0003-4000-8000-000000000003",
                "roletype": {"name": "viewer"},
                "roletypeId": "ed1707aa-0000-4000-8000-000000000002",
                "group": {
                    "id": "f2f2d33c-38ee-4f31-9426-f364bc488032",
                    "name": "Univerzita obrany",
                    "grouptype": {"name": "katedra"}
                }
            },
            {
                "id": "9f0d8dc8-725a-4c84-86fa-995feb50b749",
                "roletype": {"name": "odpovědný řešitel"},
                "roletypeId": "39be2445-f6f1-4124-bd82-00b8dd9c4bce",
                "group": {
                    "id": "007c0a9e-dabf-46de-9b8e-71ec905711d7",
                    "name": "řešitelský kolektiv",
                    "grouptype": {"name": "řešitelský kolektiv"}
                }
            }
        ]
    )


def get_miriam_jaksikova_context(async_session_maker):
    """Miriam Jakšíková - has NO roles"""
    return create_user_context(
        async_session_maker,
        user_email="Miriam.Jaksikova@world.com",
        user_id="2297fe33-4820-42c6-929a-d848e92a90e5",
        fullname="Miriam Jakšíková",
        roles=[]
    )


def get_estera_luckova_context(async_session_maker):
    """Estera Lučková - create with editor role for testing"""
    return create_user_context(
        async_session_maker,
        user_email="Estera.Luckova@world.com",
        user_id="bc0d2e4f-4db0-4c38-a3e7-d0627f68068e",
        fullname="Estera Lučková",
        roles=[
            {
                "id": "test-editor-role-001",
                "roletype": {"name": "editor"},
                "roletypeId": "ed1707aa-0001-4000-8000-000000000001",
                "group": {
                    "id": "f2f2d33c-38ee-4f31-9426-f364bc488032",
                    "name": "Univerzita obrany",
                    "grouptype": {"name": "univerzita"}
                }
            }
        ]
    )


# ===========================================================================================
# INSERT TESTS - Testing creation permissions
# ===========================================================================================

@pytest.mark.asyncio
async def test_admin_can_create_admission_application():
    """Test that John Newbie (admin) can create an admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_john_newbie_context(async_session_maker)

    mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    applicantId
                    rbacobjectId
                }
                ... on AdmissionApplicationGQLModelInsertError {
                    code
                    location
                }
            }
        }
    """

    resp = await schema.execute(mutation, context_value=context_value)

    # Should succeed
    assert resp.errors is None, f"Unexpected errors: {resp.errors}"
    assert resp.data["admissionApplicationInsert"]["__typename"] == "AdmissionApplicationGQLModel"
    assert resp.data["admissionApplicationInsert"]["applicantId"] == applicant_id


@pytest.mark.asyncio
async def test_odpovedly_resitel_can_create_admission_application():
    """Test that Oliver Hortík (odpovědný řešitel) can create an admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_oliver_hortik_context(async_session_maker)

    mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    applicantId
                }
            }
        }
    """

    resp = await schema.execute(mutation, context_value=context_value)

    assert resp.errors is None, f"Unexpected errors: {resp.errors}"
    assert resp.data["admissionApplicationInsert"]["__typename"] == "AdmissionApplicationGQLModel"


@pytest.mark.asyncio
async def test_no_role_user_cannot_create_admission_application():
    """Test that Miriam Jakšíková (no roles) cannot create an admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_miriam_jaksikova_context(async_session_maker)

    mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                }
            }
        }
    """

    resp = await schema.execute(mutation, context_value=context_value)

    # Should fail - no roles means no permissions
    assert resp.errors is not None
    error_msg = str(resp.errors[0])
    assert "Permission denied" in error_msg or "cannot create" in error_msg


# ===========================================================================================
# UPDATE TESTS - Testing creator ownership and group permissions
# ===========================================================================================

@pytest.mark.asyncio
async def test_creator_can_update_own_admission_application():
    """Test that the creator can always update their own admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_john_newbie_context(async_session_maker)

    # First, create an application
    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    lastchange
                    appliedDate
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context_value)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"

    app_id = create_resp.data["admissionApplicationInsert"]["id"]
    lastchange = create_resp.data["admissionApplicationInsert"]["lastchange"]

    # Now update it as the same user (creator)
    update_mutation = f"""
        mutation {{
            admissionApplicationUpdate(
                application: {{
                    id: "{app_id}"
                    lastchange: "{lastchange}"
                    appliedDate: "2024-01-16T10:00:00"
                }}
            ) {{
                __typename
                ... on AdmissionApplicationGQLModel {{
                    id
                    appliedDate
                }}
                ... on AdmissionApplicationGQLModelUpdateError {{
                    code
                    location
                }}
            }}
        }}
    """

    update_resp = await schema.execute(update_mutation, context_value=context_value)

    # Should succeed - creator owns the application
    assert update_resp.errors is None, f"Unexpected errors: {update_resp.errors}"
    assert update_resp.data["admissionApplicationUpdate"]["__typename"] == "AdmissionApplicationGQLModel"
    assert update_resp.data["admissionApplicationUpdate"]["appliedDate"] == "2024-01-16T10:00:00"


@pytest.mark.asyncio
async def test_same_group_user_can_update_application():
    """Test that a user with editor role in the same group can update an application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    # Create application as John (admin in Univerzita)
    context1 = get_john_newbie_context(async_session_maker)

    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    lastchange
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context1)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"

    app_id = create_resp.data["admissionApplicationInsert"]["id"]
    lastchange = create_resp.data["admissionApplicationInsert"]["lastchange"]

    # Try to update as Estera (editor in same Univerzita group)
    context2 = get_estera_luckova_context(async_session_maker)

    update_mutation = f"""
        mutation {{
            admissionApplicationUpdate(
                application: {{
                    id: "{app_id}"
                    lastchange: "{lastchange}"
                    appliedDate: "2024-01-16T10:00:00"
                }}
            ) {{
                __typename
                ... on AdmissionApplicationGQLModel {{
                    id
                    appliedDate
                }}
            }}
        }}
    """

    update_resp = await schema.execute(update_mutation, context_value=context2)

    # Should succeed - same group, has editor role
    assert update_resp.errors is None, f"Unexpected errors: {update_resp.errors}"
    assert update_resp.data["admissionApplicationUpdate"]["__typename"] == "AdmissionApplicationGQLModel"


@pytest.mark.asyncio
async def test_viewer_cannot_update_admission_application():
    """Test that Oliver (viewer role) cannot update an admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    # Create application as John (admin)
    context1 = get_john_newbie_context(async_session_maker)

    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    lastchange
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context1)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"

    app_id = create_resp.data["admissionApplicationInsert"]["id"]
    lastchange = create_resp.data["admissionApplicationInsert"]["lastchange"]

    # Try to update as Oliver who only has viewer role (his odpovědný řešitel is in different group)
    context2 = get_oliver_hortik_context(async_session_maker)

    update_mutation = f"""
        mutation {{
            admissionApplicationUpdate(
                application: {{
                    id: "{app_id}"
                    lastchange: "{lastchange}"
                    appliedDate: "2024-01-16T10:00:00"
                }}
            ) {{
                __typename
                ... on AdmissionApplicationGQLModel {{
                    id
                }}
            }}
        }}
    """

    update_resp = await schema.execute(update_mutation, context_value=context2)

    # Should fail - viewer doesn't have update permissions for this group
    assert update_resp.errors is not None
    error_msg = str(update_resp.errors[0])
    assert "Permission denied" in error_msg


# ===========================================================================================
# DELETE TESTS - Testing admin-only permissions
# ===========================================================================================

@pytest.mark.asyncio
async def test_admin_can_delete_admission_application():
    """Test that John Newbie (admin) can delete an admission application"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_john_newbie_context(async_session_maker)

    # Create application
    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    lastchange
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context_value)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"

    app_id = create_resp.data["admissionApplicationInsert"]["id"]
    lastchange = create_resp.data["admissionApplicationInsert"]["lastchange"]

    # Delete as admin
    delete_mutation = f"""
        mutation {{
            admissionApplicationDelete(
                application: {{
                    id: "{app_id}"
                    lastchange: "{lastchange}"
                }}
            ) {{
                __typename
                ... on AdmissionApplicationGQLModelDeleteError {{
                    code
                    location
                }}
            }}
        }}
    """

    delete_resp = await schema.execute(delete_mutation, context_value=context_value)

    # Should succeed - admin has delete permissions
    assert delete_resp.errors is None, f"Unexpected errors: {delete_resp.errors}"


@pytest.mark.asyncio
async def test_odpovedly_resitel_cannot_delete_admission_application():
    """Test that Oliver (odpovědný řešitel but not admin) cannot delete"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    context_value = get_oliver_hortik_context(async_session_maker)

    # Create application
    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                    lastchange
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context_value)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"

    app_id = create_resp.data["admissionApplicationInsert"]["id"]
    lastchange = create_resp.data["admissionApplicationInsert"]["lastchange"]

    # Try to delete (should fail - not admin)
    delete_mutation = f"""
        mutation {{
            admissionApplicationDelete(
                application: {{
                    id: "{app_id}"
                    lastchange: "{lastchange}"
                }}
            ) {{
                __typename
            }}
        }}
    """

    delete_resp = await schema.execute(delete_mutation, context_value=context_value)

    # Should fail - odpovědný řešitel doesn't have delete permissions
    assert delete_resp.errors is not None
    error_msg = str(delete_resp.errors[0])
    assert "Permission denied" in error_msg


# ===========================================================================================
# QUERY TESTS - Testing read permissions
# ===========================================================================================

@pytest.mark.asyncio
async def test_user_can_read_admission_applications():
    """Test that authenticated users can read admission applications"""
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    applicant_id = _uuid_to_str(data["admission_applicants"][0]["id"])
    # Create application as John
    context1 = get_john_newbie_context(async_session_maker)

    create_mutation = f"""
        mutation {
            admissionApplicationInsert(
                application: {
                    applicantId: "{applicant_id}"
                    appliedDate: "2024-01-15T10:00:00"
                }
            ) {
                __typename
                ... on AdmissionApplicationGQLModel {
                    id
                }
            }
        }
    """

    create_resp = await schema.execute(create_mutation, context_value=context1)
    assert create_resp.errors is None, f"Create failed: {create_resp.errors}"
    app_id = create_resp.data["admissionApplicationInsert"]["id"]

    # Read as Oliver (has viewer role in same group)
    context2 = get_oliver_hortik_context(async_session_maker)

    query = f"""
        query {{
            admissionApplicationById(id: "{app_id}") {{
                id
                applicantId
            }}
        }}
    """

    query_resp = await schema.execute(query, context_value=context2)

    # Should succeed - can read
    assert query_resp.errors is None, f"Unexpected errors: {query_resp.errors}"
    assert query_resp.data["admissionApplicationById"]["id"] == app_id
    assert query_resp.data["admissionApplicationById"]["applicantId"] == applicant_id
