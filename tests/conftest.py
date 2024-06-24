import json
from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from tests.apps.django_app import django_asgi_app
from tests.apps.fastapi_app import get_fast_api_app

BASE_PATH = Path(__file__).absolute().parent


@pytest.fixture()
def django_app():
    return django_asgi_app


class AsyncContextManager:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


@pytest.fixture()
def mock_lifespan():
    return Mock()


@pytest.fixture()
def fastapi_app(mock_lifespan):
    @asynccontextmanager
    async def life(app):
        mock_lifespan(app, "startup")
        yield
        mock_lifespan(app, "shutdown")

    return get_fast_api_app(lifespan_func=life)


@pytest.fixture(scope="session")
def load_lambda_events():
    examples = {}
    for example_file in BASE_PATH.glob("event_examples/*"):
        if example_file.is_file():
            with open(example_file) as f:
                examples[example_file.stem] = json.load(f)
    return examples


@pytest.fixture()
def lambda_events(load_lambda_events):
    return deepcopy(load_lambda_events)
