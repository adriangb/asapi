from __future__ import annotations

import anyio
import uvicorn
from fastapi import FastAPI

from asapi._injected import validate_injections
from asapi._signal_handling import handle_signals


async def serve(app: FastAPI, port: int) -> None:  # pragma: no cover
    """Serve an ASGI application."""
    validate_injections(app)

    config = uvicorn.Config(app, port=port, host="0.0.0.0", log_config=None)
    server = uvicorn.Server(config=config)

    async with handle_signals() as stop:
        async with anyio.create_task_group() as tg:
            tg.start_soon(server.serve)
            await stop.wait()
            if server.started:
                await server.shutdown()
