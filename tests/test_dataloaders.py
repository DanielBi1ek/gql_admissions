import pytest
import logging

from .shared import (
    createInfo,
    prepare_in_memory_sqllite
)

from uoishelpers.resolvers import getUserFromInfo


@pytest.mark.asyncio
async def test_get_user():
    asyncSessionMaker = await prepare_in_memory_sqllite()
    info = createInfo(asyncSessionMaker=asyncSessionMaker, withuser=True)

    user = getUserFromInfo(info)
    logging.info(user)
    assert user is not None


@pytest.mark.asyncio
async def test_get_user_none():
    asyncSessionMaker = await prepare_in_memory_sqllite()
    info = createInfo(asyncSessionMaker=asyncSessionMaker, withuser=False)

    with pytest.raises(AssertionError, match="User is wanted but not present"):
        getUserFromInfo(info)
