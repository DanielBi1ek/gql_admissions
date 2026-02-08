import pytest
import pytest_asyncio

from .shared import drain_session_cleanups


@pytest_asyncio.fixture(autouse=True)
async def close_loader_sessions():
    yield
    await drain_session_cleanups()
