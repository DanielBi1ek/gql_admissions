import logging
import sqlalchemy

from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from .BaseModel import BaseModel
from .EventDBModel import EventModel
from .EventInvitationModel import EventInvitationModel
from .AdmissionModel import AdmissionModel
from .EnrollmentModel import EnrollmentModel
from .PaymentModel import PaymentModel
# from .StateModel import StateModel  # StateModel intentionally not imported — we keep models simple/no enforced FK to 'states'


async def startEngine(connectionstring, makeDrop=False, makeUp=True):
    """Provede nezbytne ukony a vrati asynchronni SessionMaker"""
    asyncEngine = create_async_engine(connectionstring)

    async with asyncEngine.begin() as conn:
        if makeDrop:
            # Drop entire public schema with CASCADE to remove dependent objects that would
            # block dropping individual tables (useful for dev/demo environments).
            def _drop_schema(sync_conn):
                try:
                    sync_conn.execute(sqlalchemy.text("DROP SCHEMA public CASCADE"))
                    sync_conn.execute(sqlalchemy.text("CREATE SCHEMA public"))
                except Exception:
                    # fallback to metadata.drop_all if schema operations are not allowed
                    BaseModel.metadata.drop_all(sync_conn)

            await conn.run_sync(_drop_schema)
            print("public schema dropped and recreated (CASCADE)")
        if makeUp:
            try:
                await conn.run_sync(BaseModel.metadata.create_all)
                print("BaseModel.metadata.create_all finished")
            except sqlalchemy.exc.NoReferencedTableError as e:
                print(e)
                print("Unable automaticaly create tables")
                return None

    async_sessionMaker = sessionmaker(
        asyncEngine, expire_on_commit=False, class_=AsyncSession
    )
    return async_sessionMaker

import os

def ComposeConnectionString():
    """Odvozuje connectionString z promennych prostredi (nebo z Docker Envs, coz je fakticky totez).
    Lze predelat na napr. konfiguracni file.
    """
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "example")
    database = os.environ.get("POSTGRES_DB", "data")
    hostWithPort = os.environ.get("POSTGRES_HOST", "localhost:5432")

    driver = "postgresql+asyncpg"  # "postgresql+psycopg2"
    connectionstring = f"{driver}://{user}:{password}@{hostWithPort}/{database}"
    connectionstring = os.environ.get("CONNECTION_STRING", connectionstring)

    return connectionstring
