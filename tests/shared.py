import sqlalchemy
import sys
import asyncio
import os
import uuid
import datetime

_SESSION_CLEANERS = []

os.environ.setdefault("DEMO", "False")
os.environ.setdefault("GQLUG_ENDPOINT_URL", "http://localhost:33001/api/ug")


def is_federation_mode() -> bool:
    return os.environ.get("TEST_TARGET", "").strip().lower() == "federation"


def _ensure_uuid(value):
    if value is None or value is uuid.UUID:
        return value
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _coerce_uuid_fields(data_dict):
    result = dict(data_dict)
    for key, value in list(result.items()):
        if value is None or isinstance(value, uuid.UUID):
            continue
        if not isinstance(value, str):
            continue
        key_lower = key.lower()
        if key_lower == "id" or key_lower.endswith("_id"):
            try:
                result[key] = uuid.UUID(value)
            except ValueError:
                continue
    return result


# setting path
sys.path.append("../")

import pytest

from src.DBDefinitions import (
    BaseModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    AdmissionApplicantModel,
    AdmissionPaymentModel,
    AdmissionPaymentInfoModel,
    AdmissionBankAccountModel,
    AdmissionOfferModel,
    StudyProgramModel,
    BankStatementModel,
    UserModel,
)


def register_session_cleanup(closer):
    _SESSION_CLEANERS.append(closer)


async def drain_session_cleanups():
    while _SESSION_CLEANERS:
        closer = _SESSION_CLEANERS.pop()
        await closer()


async def prepare_in_memory_sqllite():
    if is_federation_mode():
        return None

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    asyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    register_session_cleanup(asyncEngine.dispose)
    async with asyncEngine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async_session_maker = sessionmaker(
        asyncEngine, expire_on_commit=False, class_=AsyncSession
    )

    return async_session_maker


def _parse_iso_datetime(value):
    """Parse ISO format datetime string to Python datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str):
        try:
            # Handle ISO format with or without microseconds
            return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return value
    return value


def _parse_datetime_fields(data_dict):
    """Parse all datetime fields in a dictionary."""
    datetime_fields = [
        "created", "lastchange", "application_start_date", "application_end_date",
        "applied_date", "accepted_at", "withdrawn_at", "paid_at"
    ]
    result = dict(data_dict)
    for field in datetime_fields:
        if field in result:
            result[field] = _parse_iso_datetime(result[field])
    return _coerce_uuid_fields(result)


def get_demodata():
    from uoishelpers.dataloaders import readJsonFile
    data = readJsonFile(jsonFileName="./systemdata.json")

    # Parse datetime fields in all tables
    for table_name in data:
        if isinstance(data[table_name], list):
            data[table_name] = [_parse_datetime_fields(row) for row in data[table_name]]
        elif isinstance(data[table_name], dict):
            data[table_name] = _parse_datetime_fields(data[table_name])

    return data


async def prepare_demodata(async_session_maker):
    if is_federation_mode():
        return

    data = get_demodata()

    from uoishelpers.feeders import ImportModels

    await ImportModels(
        async_session_maker,
        [
            UserModel,
            StudyProgramModel,
            AdmissionBankAccountModel,
            AdmissionPaymentInfoModel,
            AdmissionOfferModel,
            BankStatementModel,
            AdmissionPaymentModel,
            AdmissionProcessModel,
            AdmissionApplicantModel,
            AdmissionApplicationModel,
        ],
        data,
    )


from src.Dataloaders import LoaderMap


def assert_no_graphql_errors(response):
    """Assert that there are no GraphQL errors in the response."""
    assert response.errors is None, f"GraphQL errors: {response.errors}"


async def execute_gql(schema, query, context_value, variables=None):
    """Execute a GraphQL query and return the response."""
    response = await schema.execute(
        query,
        context_value=context_value,
        variable_values=variables or {}
    )
    session = context_value.get("_session")
    if session is not None:
        if response.errors:
            await session.rollback()
        elif context_value.get("_transaction_failed"):
            await session.rollback()
            context_value.pop("_transaction_failed", None)
        else:
            await session.commit()
    return response


# Admin user ID from environment or default
ADMIN_GROUP_ID = os.environ.get("ADMISSIONS_ADMIN_GROUP_ID", "cd49e152-610c-11ed-9f17-001a7dda7110")
ADMIN_ROLETYPE_ID = os.environ.get("ADMISSIONS_ADMIN_ROLETYPE_ID", "ced46aa4-3217-4fc1-b79d-f6be7d21c6b6")


class ProfilingCounter:
    """
    Mock counter object that mimics the ProfilingExtension.counter interface.
    The real counter is created by uoishelpers.schema.ProfilingExtension.
    """
    def __init__(self):
        self._data = {"total": {"count": 0, "sum": 0, "values": []}}

    def count(self, key, duration):
        """Record a count and duration for a given key."""
        if key not in self._data:
            self._data[key] = {"count": 0, "sum": 0, "values": []}
        self._data[key]["count"] += 1
        self._data[key]["sum"] += duration
        self._data[key]["values"].append(duration)

    def result(self):
        return self._data

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value


def createLoadersContext(asyncSessionMaker):
    """Create loaders context with an actual session (not session maker)."""
    if is_federation_mode():
        return {"_skip_whoami": True}

    # Create a session from the session maker
    session = asyncSessionMaker()
    loaders = LoaderMap(session)
    register_session_cleanup(session.close)
    return {"loaders": loaders, "_session": session, "_skip_whoami": True}


def createContext(asyncSessionMaker, withuser=True, user_role=None):
    """
    Create a context for GraphQL execution.

    Args:
        asyncSessionMaker: The async session maker
        withuser: Whether to include a user in the context
        user_role: Optional role type - "admin" or "administrátor" makes the user an admin
    """
    loadersContext = createLoadersContext(asyncSessionMaker)
    # Hint for federation-mode adapter which credentials to use.
    if user_role in ["admin", "administrátor", "administrator"]:
        loadersContext["_federation_user_kind"] = "admin"
    elif not withuser:
        loadersContext["_federation_user_kind"] = "anonymous"
    else:
        loadersContext["_federation_user_kind"] = "default"

    # Add extension context keys required by uoishelpers extensions
    # ProfilingExtension.counter needs to be an object with .result() method
    loadersContext["ProfilingExtension.counter"] = ProfilingCounter()

    # Default regular user
    user = {
        "id": str(_ensure_uuid("2d9dc5ca-a4a2-11ed-b9df-0242ac120003")),
        "name": "John",
        "surname": "Newbie",
        "email": "john.newbie@world.com",
        "roles": []
    }

    # If admin role requested, add appropriate roles
    if user_role in ["admin", "administrátor", "administrator"]:
        user["roles"] = [
            {
                "valid": True,
                "group": {"id": str(_ensure_uuid(ADMIN_GROUP_ID)), "name": "Admission Admins"},
                "roletype": {"id": str(_ensure_uuid(ADMIN_ROLETYPE_ID)), "name": "administrátor"}
            }
        ]

    if withuser:
        loadersContext["user"] = user
    else:
        loadersContext["user"] = None
        loadersContext["_allow_anonymous"] = True

    loadersContext["_skip_whoami"] = True
    return loadersContext


def createAdminContext(asyncSessionMaker):
    """Create a context with an admin user."""
    return createContext(asyncSessionMaker, withuser=True, user_role="admin")


def createRegularUserContext(asyncSessionMaker, user_id=None, name=None, surname=None, email=None):
    """Create a context with a regular (non-admin) user."""
    loadersContext = createLoadersContext(asyncSessionMaker)

    # Add extension context keys
    loadersContext["ProfilingExtension.counter"] = ProfilingCounter()

    user_id_value = user_id or "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
    loadersContext["_federation_user_kind"] = (
        "default"
        if str(user_id_value) == "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
        else "other"
    )
    user = {
        "id": str(_ensure_uuid(user_id_value)),
        "name": name or "John",
        "surname": surname or "Newbie",
        "email": email or "john.newbie@world.com",
        "roles": []
    }

    loadersContext["user"] = user
    loadersContext["_skip_whoami"] = True
    return loadersContext


def createApplicantContext(asyncSessionMaker, applicant_user_id):
    """Create a context with a specific applicant user."""
    data = get_demodata()
    applicants = data.get("admission_applicants", [])

    # Find the applicant to get their details (compare as strings to handle UUID/string mismatch)
    applicant = next(
        (a for a in applicants if str(a.get("applicant_user_id")) == str(applicant_user_id)),
        None
    )

    loadersContext = createLoadersContext(asyncSessionMaker)
    loadersContext["_federation_user_kind"] = "default"

    # Add extension context keys
    loadersContext["ProfilingExtension.counter"] = ProfilingCounter()

    applicant_user_uuid = str(_ensure_uuid(applicant_user_id))
    user = {
        "id": applicant_user_uuid,
        "name": applicant.get("firstname", "Test") if applicant else "Test",
        "surname": applicant.get("lastname", "User") if applicant else "User",
        "email": applicant.get("email", "test@example.com") if applicant else "test@example.com",
        "roles": []
    }

    loadersContext["user"] = user
    loadersContext["_skip_whoami"] = True
    return loadersContext


def createUnauthenticatedContext(asyncSessionMaker):
    """Create a context without a user (unauthenticated)."""
    ctx = createContext(asyncSessionMaker, withuser=False)
    ctx["_federation_user_kind"] = "anonymous"
    return ctx


def createInfo(asyncSessionMaker, withuser=True, user_role=None):
    class Request():
        @property
        def headers(self):
            return {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}

        @property
        def scope(self):
            return {"type": "http"}

    class Info():
        @property
        def context(self):
            context = createContext(asyncSessionMaker, withuser=withuser, user_role=user_role)
            context["request"] = Request()
            return context

    return Info()


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())
