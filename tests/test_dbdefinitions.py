import pytest

from src.DBDefinitions import BaseModel, ComposeConnectionString, startEngine
from src.DBFeeder import initDB
from .shared import prepare_demodata, prepare_in_memory_sqllite


@pytest.mark.asyncio
async def test_load_demo_data():
    async_session_maker = await prepare_in_memory_sqllite()
    await prepare_demodata(async_session_maker)


def test_connection_string():
    connectionString = ComposeConnectionString()
    assert "://" in connectionString
    assert "@" in connectionString


@pytest.mark.asyncio
async def test_table_start_engine():
    connectionString = "sqlite+aiosqlite:///:memory:"
    async_session_maker = await startEngine(connectionString, makeDrop=True, makeUp=True)
    assert async_session_maker is not None


@pytest.mark.asyncio
async def test_initDB():
    connectionString = "sqlite+aiosqlite:///:memory:"
    async_session_maker = await startEngine(connectionString, makeDrop=True, makeUp=True)
    assert async_session_maker is not None
    await initDB(async_session_maker)


def test_metadata_tables_present():
    table_names = set(BaseModel.metadata.tables.keys())
    expected = {
        "admission_processes",
        "admission_applications",
        "admission_payment_infos",
        "admission_payments",
        "bank_statement_payments",
        "study_programs",
        "exams",
    }
    assert expected.issubset(table_names)
