#!/usr/bin/env -S uv run --script

from __future__ import annotations

import logging
import sys

import anyio
from fastapi import APIRouter, FastAPI
from httpx import AsyncClient
from typing_extensions import TypedDict

from asapi import FromPath, Injected, bind, serve

router = APIRouter()


class EchoResponse(TypedDict):
    name: str


@router.get("/echo/{name}")
async def echo(name: FromPath[str], client: Injected[AsyncClient]) -> EchoResponse:
    resp = await client.get("https://httpbin.org/get", params={"name": name})
    resp.raise_for_status()
    return {"name": resp.json()["args"]["name"]}


def create_app(client: AsyncClient) -> FastAPI:
    app = FastAPI()
    bind(app, AsyncClient, client)
    app.include_router(router)
    return app


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    print("Starting server")

    async with AsyncClient() as client:
        app = create_app(client)
        await serve(app, int(sys.argv[1] if len(sys.argv) > 1 else 8000))
        print("Shutdown initiated")

    print("Shutdown complete")


if __name__ == "__main__":
    anyio.run(main)
