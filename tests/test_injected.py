import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from asapi import Injected, bind, validate_injections


class Thing:
    def __init__(self, x: int) -> None:
        self.x = x


def test_injection() -> None:
    app = FastAPI()

    @app.get("/")
    async def get_root(thing: Injected[Thing]) -> int:  # type: ignore
        return thing.x

    bind(app, Thing, Thing(123))

    validate_injections(app)

    client = TestClient(app)

    assert client.get("/").json() == 123


def test_injectino_router() -> None:
    router = APIRouter()

    @router.get("/")
    async def get_root(thing: Injected[Thing]) -> int:  # type: ignore
        return thing.x

    app = FastAPI()
    app.include_router(router)
    bind(app, Thing, Thing(123))

    validate_injections(app)

    client = TestClient(app)

    assert client.get("/").json() == 123


def test_missing_injection() -> None:
    app = FastAPI()

    @app.get("/")
    async def get_root(thing: Injected[Thing]) -> int:  # type: ignore
        ...

    with pytest.raises(RuntimeError, match="Missing dependency"):
        validate_injections(app)


def test_missing_injections_router() -> None:
    router = APIRouter()

    @router.get("/")
    async def get_root(thing: Injected[Thing]) -> int:  # type: ignore
        ...

    app = FastAPI()
    app.include_router(router)

    with pytest.raises(RuntimeError, match="Missing dependency"):
        validate_injections(app)


def test_run_without_validating() -> None:
    app = FastAPI()

    @app.get("/")
    async def get_root(thing: Injected[Thing]) -> int:  # type: ignore
        ...

    client = TestClient(app)

    with pytest.raises(RuntimeError, match="No dependency override found"):
        client.get("/")
