from __future__ import annotations

import anyio
from fastapi import FastAPI
import uvicorn
from starlette.types import ASGIApp

from asapi._injected import validate_injections
from asapi._signal_handling import handle_signals


def _validate_injections(app: ASGIApp) -> None:
    """Try to find the FastAPI app, possibly wrapped in middleware, and validate its dependencies."""
    if isinstance(app, FastAPI):
        validate_injections(app)
    else:
        # having the original app under `.app` is a common pattern in middleware
        # but not a standard, so we need to fail gracefully
        maybe_app = getattr(app, "app", None)
        if maybe_app is not None:
            validate_injections(maybe_app)


async def serve(app: ASGIApp, port: int) -> None:  # pragma: no cover
    """Serve an ASGI application."""
    _validate_injections(app)

    config = uvicorn.Config(app, port=port, host="0.0.0.0", log_config=None)
    server = uvicorn.Server(config=config)

    async with handle_signals() as stop:
        async with anyio.create_task_group() as tg:
            tg.start_soon(server.serve)
            await stop.wait()
            if server.started:
                await server.shutdown()
