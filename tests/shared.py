import pytest

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.DBDefinitions import (
    BaseModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    AdmissionPaymentModel,
    AdmissionPaymentInfoModel,
    AdmissionBankAccountModel,
    AdmissionOfferModel,
    StudyProgramModel,
    BankStatementModel,
    AdmissionApplicantModel,
)
from src.DBFeeder import get_demodata
from src.Dataloaders import createLoadersContext


async def prepare_in_memory_sqllite():
    async_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async_session_maker = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    return async_session_maker


class SessionMakerWrapper:
    """Wrapper that makes a sessionmaker look like a session for loaders"""

    def __init__(self, sessionmaker):
        self._sessionmaker = sessionmaker
        self._session = None

    async def get_session(self):
        """Get or create a session"""
        if self._session is None:
            self._session = self._sessionmaker()
        return self._session

    @property
    def identity_map(self):
        """Proxy to session's identity_map"""
        # Return a dummy dict-like object for testing
        class DummyIdentityMap(dict):
            def get(self, key, default=None):
                return default

        return DummyIdentityMap()

    async def execute(self, statement):
        """Proxy to session's execute method"""
        session = await self.get_session()
        return await session.execute(statement)


def createContext(asyncSessionMaker, withuser=True, user_role="administrátor", roles=None, user_id=None):
    """
    Create context for testing with admissions RBAC.

    Args:
        asyncSessionMaker: Async session maker for database access
        withuser: Whether to include a user in the context
        user_role: Legacy role hint ("administrátor" => admissions admin, other => no roles)
        roles: Explicit roles list (overrides user_role)
        user_id: Explicit user id for context
    """
    from src.GraphTypeDefinitions.admission_permissions import AdmissionsAdminPermission

    loadersContext = createLoadersContext(asyncSessionMaker)

    if roles is None:
        if user_role in ["administrátor", "admin"]:
            roles = [{
                "group": {"id": AdmissionsAdminPermission.GROUP_ID},
                "roletype": {"id": AdmissionsAdminPermission.ROLETYPE_ID},
            }]
        else:
            roles = []

    user_id = user_id or "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
    user = {
        "id": user_id,
        "name": "John",
        "surname": "Newbie",
        "email": "john.newbie@world.com",
        "roles": roles,
    }

    if withuser:
        loadersContext["user"] = user
    # Store the sessionmaker for later use by resolvers and extensions
    loadersContext["asyncSessionMaker"] = asyncSessionMaker
    # Also store it as the session for compatibility with extensions
    loadersContext["session"] = asyncSessionMaker
    return loadersContext


def createInfo(asyncSessionMaker, withuser=True, user_role="administrátor", roles=None, user_id=None):
    class Request:
        def __init__(self, user_data=None):
            self.scope = {
                "type": "http",
                "headers": [(b"authorization", b"Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003")],
                "user": user_data,
            }

        @property
        def headers(self):
            return {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}

    class Info:
        def __init__(self, request_obj, context_dict):
            self._request = request_obj
            self._context = context_dict

        @property
        def context(self):
            return self._context

        @property
        def request(self):
            return self._request

    context = createContext(
        asyncSessionMaker,
        withuser=withuser,
        user_role=user_role,
        roles=roles,
        user_id=user_id
    )
    user_data = context.get("user") if withuser else None
    request_obj = Request(user_data)
    context["request"] = request_obj

    return Info(request_obj, context)


async def prepare_demodata(async_session_maker):
    data = get_demodata()
    import datetime as _dt

    # Parse ISO format dates with microsecond precision
    def _parse_iso(v):
        if isinstance(v, str):
            try:
                return _dt.datetime.fromisoformat(v)
            except (ValueError, TypeError):
                try:
                    v_clean = v.rstrip("Z")
                    return _dt.datetime.strptime(v_clean, "%Y-%m-%dT%H:%M:%S.%f")
                except (ValueError, TypeError):
                    return v
        return v

    if isinstance(data, dict):
        if "admission_offers" not in data and "exams" in data:
            data["admission_offers"] = data.pop("exams")
        if "bank_statements" not in data and "bank_statement_payments" in data:
            data["bank_statements"] = data.pop("bank_statement_payments")

    # Parse dates in admission offers
    if isinstance(data, dict) and "admission_offers" in data:
        for row in data.get("admission_offers", []):
            if not isinstance(row, dict):
                continue
            for key in [
                "application_start_date",
                "application_end_date",
                "created",
                "lastchange",
            ]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    # Parse dates in admission_applications
    if isinstance(data, dict) and "admission_applications" in data:
        for row in data.get("admission_applications", []):
            if not isinstance(row, dict):
                continue
            for key in [
                "applied_date",
                "accepted_at",
                "withdrawn_at",
                "created",
                "lastchange",
            ]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    # Parse dates in admission_payments
    if isinstance(data, dict) and "admission_payments" in data:
        for row in data.get("admission_payments", []):
            if not isinstance(row, dict):
                continue
            if "bank_payment_id" in row and "bank_statement_id" not in row:
                row["bank_statement_id"] = row.pop("bank_payment_id")
            for key in ["paid_at", "created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    # Parse dates in admission_payment_infos
    if isinstance(data, dict) and "admission_payment_infos" in data:
        for row in data.get("admission_payment_infos", []):
            if not isinstance(row, dict):
                continue
            for key in ["created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    # Parse dates in admission_applicants
    if isinstance(data, dict) and "admission_applicants" in data:
        for row in data.get("admission_applicants", []):
            if not isinstance(row, dict):
                continue
            for key in ["created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    # Parse dates in admission_bank_accounts
    if isinstance(data, dict) and "admission_bank_accounts" in data:
        for row in data.get("admission_bank_accounts", []):
            if not isinstance(row, dict):
                continue
            for key in ["created", "lastchange"]:
                if key in row:
                    row[key] = _parse_iso(row.get(key))

    from uoishelpers.feeders import ImportModels

    await ImportModels(
        async_session_maker,
        [
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
