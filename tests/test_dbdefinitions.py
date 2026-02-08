import sqlalchemy
from sqlalchemy import select
import sys
import asyncio

import pytest

from .shared import prepare_demodata, prepare_in_memory_sqllite, get_demodata
from src.DBDefinitions import BaseModel, ComposeConnectionString, startEngine


@pytest.mark.asyncio
async def test_load_demo_data():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)

    data = get_demodata()
    assert data is not None
    assert "admission_offers" in data
    assert "admission_applicants" in data
    assert "admission_applications" in data


def test_connection_string():
    connectionString = ComposeConnectionString()

    assert "://" in connectionString


@pytest.mark.asyncio
async def test_table_start_engine():
    connectionString = "sqlite+aiosqlite:///:memory:"
    async_session_maker = await startEngine(
        connectionString, makeDrop=True, makeUp=True
    )

    assert async_session_maker is not None


from src.DBFeeder import initDB


@pytest.mark.asyncio
async def test_init_db():
    connectionString = "sqlite+aiosqlite:///:memory:"
    async_session_maker = await startEngine(
        connectionString, makeDrop=True, makeUp=True
    )

    # initDB requires DEMODATA environment variable
    import os

    os.environ["DEMODATA"] = "True"

    await initDB(async_session_maker)

    # Clean up
    del os.environ["DEMODATA"]
