from __future__ import annotations
from contextlib import ExitStack
import signal
import sys

import anyio
from fastapi import FastAPI
import uvicorn
from starlette.types import ASGIApp

from asapi._injected import validate_injections


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

    # Note: we don't actually use `anyio`'s signal handling here
    # We only want to override the default behavior of the event loop
    # which is to raise a `CancelledError` on SIGINT/SIGTERM
    with ExitStack() as stack:
        if sys.platform != "win32":
            stack.enter_context(
                anyio.open_signal_receiver(signal.SIGINT, signal.SIGTERM)
            )
        with server.capture_signals():
            await server.serve()
