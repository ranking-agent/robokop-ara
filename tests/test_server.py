"""Test the server."""
from contextlib import asynccontextmanager, AsyncExitStack
from datetime import datetime
from functools import partial, wraps
from typing import Callable

from asgiar import ASGIAR
from fastapi import FastAPI
import httpx
import pytest
from reasoner_pydantic import Query

from app.server import APP


def with_context(context, *args_, **kwargs_):
    """Turn context manager into decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with context(*args_, **kwargs_):
                await func(*args, **kwargs)
        return wrapper
    return decorator


@asynccontextmanager
async def function_overlay(host: str, fcn: Callable):
    """Apply an ASGIAR overlay that runs `fcn` for all routes."""
    async with AsyncExitStack() as stack:
        app = FastAPI()

        # pylint: disable=unused-variable disable=unused-argument
        @app.api_route(
            "/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE"],
        )
        async def all_paths(path: str, request: Query):
            return fcn(request.dict())

        await stack.enter_async_context(
            ASGIAR(app, host=host)
        )
        yield


with_function_overlay = partial(with_context, function_overlay)

client = httpx.AsyncClient(app=APP, base_url="http://test")


@pytest.mark.asyncio
@with_function_overlay(
    "automat.renci.org",
    lambda request: request | {
        "automat": request.get("automat", []) + [datetime.now().isoformat()]
    },
)
@with_function_overlay(
    "aragorn-ranker.renci.org",
    lambda request: request | {
        "ranker": request.get("ranker", []) + [datetime.now().isoformat()]
    },
)
async def test_server():
    """Test the server."""
    payload = {"message": {}}
    response = await client.post("/query", json=payload)
    response.raise_for_status()
    output = response.json()
    assert len(output.get("automat")) == 1
    assert len(output.get("ranker")) == 3
    assert all(
        output.get("automat")[0] < ranker_ts
        for ranker_ts in output.get("ranker")
    )


@pytest.mark.asyncio
async def test_endpoint():
    """Test getting OpenAPI."""
    response = await client.get(
        "/openapi.json",
    )
    response.raise_for_status()
    # and again, to make sure the caching works
    response = await client.get(
        "/openapi.json",
    )
    response.raise_for_status()
