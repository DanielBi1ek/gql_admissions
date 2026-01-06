import pytest
import uuid

from uoishelpers.resolvers import getLoadersFromInfo, getUserFromInfo

from .shared import createInfo, prepare_demodata, prepare_in_memory_sqllite
from src.DBFeeder import get_demodata


@pytest.mark.asyncio
async def test_get_user():
    info = createInfo(asyncSessionMaker=None, withuser=False)
    user = getUserFromInfo(info)
    assert user is not None


@pytest.mark.asyncio
async def test_loader_fetch_admission_process():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    process_id = uuid.UUID(data["admission_processes"][0]["id"])

    info = createInfo(asyncSessionMaker=async_session_maker, withuser=True)
    loaders = getLoadersFromInfo(info)
    row = await loaders.AdmissionProcessModel.load(process_id)
    assert row is not None
