import pytest
import uuid

from uoishelpers.resolvers import getLoadersFromInfo, getUserFromInfo

from .shared import createInfo, prepare_demodata, prepare_in_memory_sqllite, SessionMakerWrapper
from src.DBFeeder import get_demodata


@pytest.mark.asyncio
async def test_get_user():
    # Test with withuser=True to ensure user is found
    info = createInfo(asyncSessionMaker=None, withuser=True)
    user = getUserFromInfo(info)
    assert user is not None


@pytest.mark.asyncio
async def test_loader_fetch_admission_process():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    process_id_raw = data["admission_processes"][0]["id"]
    # Handle both string and UUID object cases
    process_id = uuid.UUID(process_id_raw) if isinstance(process_id_raw, str) else process_id_raw

    # Create a proper session for the loader
    session = async_session_maker()

    from src.Dataloaders import LoaderMap
    loaders = LoaderMap(session)

    row = await loaders.AdmissionProcessModel.load(process_id)
    assert row is not None
