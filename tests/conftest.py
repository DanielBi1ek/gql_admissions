import os
from types import SimpleNamespace

import aiohttp
import pytest
import pytest_asyncio

from .shared import drain_session_cleanups, is_federation_mode


_TOKEN_CACHE = {}

def _credentials_from_context(context: dict):
    kind = (context or {}).get("_federation_user_kind") or "default"
    if kind == "anonymous":
        return None

    if kind == "admin":
        admin_username = os.environ.get("TEST_ADMIN_USERNAME")
        admin_password = os.environ.get("TEST_ADMIN_PASSWORD")
        if not admin_username or not admin_password:
            pytest.skip(
                "TEST_TARGET=federation and admin scenario requires "
                "TEST_ADMIN_USERNAME + TEST_ADMIN_PASSWORD"
            )
        return admin_username, admin_password

    if kind == "other":
        other_username = os.environ.get("TEST_OTHER_USERNAME")
        other_password = os.environ.get("TEST_OTHER_PASSWORD")
        if not other_username or not other_password:
            pytest.skip(
                "TEST_TARGET=federation and non-owner scenario requires "
                "TEST_OTHER_USERNAME + TEST_OTHER_PASSWORD"
            )
        return other_username, other_password

    return (
        os.environ.get("TEST_USERNAME", "john.newbie@world.com"),
        os.environ.get("TEST_PASSWORD", "john.newbie@world.com"),
    )


async def _get_token(username: str, password: str) -> str:
    cache_key = f"{username}:{password}"
    cached = _TOKEN_CACHE.get(cache_key)
    if cached is not None:
        return cached

    oauth_url = os.environ.get("OAUTH_URL", "http://localhost:33001/oauth/login3")
    async with aiohttp.ClientSession() as session:
        async with session.get(oauth_url) as resp:
            if resp.status != 200:
                text = await resp.text()
                pytest.fail(f"Cannot obtain OAuth key ({resp.status}) from {oauth_url}: {text}")
            key_payload = await resp.json(content_type=None)
        payload = {
            "key": key_payload["key"],
            "username": username,
            "password": password,
        }
        async with session.post(oauth_url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                pytest.fail(f"Cannot login as {username} ({resp.status}): {text}")
            token_payload = await resp.json(content_type=None)

    token = token_payload.get("token")
    if not token:
        pytest.fail(f"OAuth token missing for user {username}")
    _TOKEN_CACHE[cache_key] = token
    return token


async def _execute_over_federation(query, context_value=None, variable_values=None, **_kwargs):
    gql_url = os.environ.get("GQL_URL", "http://localhost:33001/api/gql")
    # Apollo gateway in this stack does not expose `_entities` to clients, but the
    # admissions subgraph does. Route these federation-internal queries directly
    # to the subgraph so resolve_reference tests can run in federation mode.
    if "_entities" in (query or ""):
        gql_url = os.environ.get("SUBGRAPH_ADMISSIONS_URL", "http://localhost:8001/gql")
    credentials = _credentials_from_context(context_value or {})

    cookies = {}
    if credentials is not None:
        token = await _get_token(*credentials)
        cookies["authorization"] = token

    payload = {
        "query": query,
        "variables": variable_values or {},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(gql_url, json=payload, cookies=cookies) as resp:
            try:
                response_payload = await resp.json(content_type=None)
            except Exception:
                text = await resp.text()
                response_payload = {"errors": [{"message": f"HTTP {resp.status}: {text}"}]}

    return SimpleNamespace(
        data=response_payload.get("data"),
        errors=response_payload.get("errors"),
    )


@pytest.fixture(autouse=True)
def patch_schema_execute_for_federation(monkeypatch):
    if not is_federation_mode():
        return

    from src.GraphTypeDefinitions import schema

    monkeypatch.setattr(schema, "execute", _execute_over_federation)


def pytest_collection_modifyitems(config, items):
    if not is_federation_mode():
        return

    local_only_paths = {
        "tests/test_client.py",
        "tests/test_dbdefinitions.py",
        "tests/test_dataloaders.py",
    }
    skip_local = pytest.mark.skip(reason="Skipped in TEST_TARGET=federation (local-only test)")

    for item in items:
        path = str(item.fspath)
        if any(path.endswith(local_path) for local_path in local_only_paths):
            item.add_marker(skip_local)


@pytest_asyncio.fixture(autouse=True)
async def close_loader_sessions():
    yield
    await drain_session_cleanups()
