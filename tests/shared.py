import pytest

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.DBDefinitions import (
    BaseModel,
    EventModel,
    EventInvitationModel,
    StudyProgramModel,
    AdmissionProcessModel,
    AdmissionApplicationModel,
    EnrollmentModel,
    PaymentInfoModel,
    PaymentModel,
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


async def prepare_demodata(async_session_maker):
    data = get_demodata()
    from uoishelpers.feeders import ImportModels

    await ImportModels(
        async_session_maker,
        [
            PaymentInfoModel,
            StudyProgramModel,
            AdmissionProcessModel,
            AdmissionApplicationModel,
            EnrollmentModel,
            PaymentModel,
            EventModel,
            EventInvitationModel,
        ],
        data,
    )


def createContext(asyncSessionMaker, withuser=True):
    loadersContext = createLoadersContext(asyncSessionMaker)
    user = {
        "id": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
        "name": "John",
        "surname": "Newbie",
        "email": "john.newbie@world.com",
    }
    if withuser:
        loadersContext["user"] = user
    return loadersContext


def createInfo(asyncSessionMaker, withuser=True):
    class Request:
        @property
        def headers(self):
            return {"Authorization": "Bearer 2d9dc5ca-a4a2-11ed-b9df-0242ac120003"}

    class Info:
        @property
        def context(self):
            context = createContext(asyncSessionMaker, withuser=withuser)
            context["request"] = Request()
            return context

    return Info()
