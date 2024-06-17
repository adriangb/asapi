import asyncio
import signal
from contextlib import asynccontextmanager
from logging import getLogger
from typing import AsyncIterator
from weakref import WeakKeyDictionary

import anyio

logger = getLogger(__name__)


SIGNAL_HANDLERS: WeakKeyDictionary[asyncio.AbstractEventLoop, anyio.Event] = (
    WeakKeyDictionary()
)


async def _signal_handler(stop: anyio.Event) -> None:
    with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
        async for _ in signals:
            logger.info("Received shutdown signal")
            stop.set()
            return


@asynccontextmanager
async def handle_signals() -> AsyncIterator[anyio.Event]:
    """Handle SIGTERM and SIGINT signals.

    This context manager provides an anyio Event that gets set when a signal is received and we are shutting down.
    """
    # asyncio only allows one signal handler per event loop, so we need to
    # check if we're in an asyncio event loop and if so, reuse the existing
    # stop event
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # we're not in an asyncio event loop
        loop = None
    if loop and loop in SIGNAL_HANDLERS:
        yield SIGNAL_HANDLERS[loop]
        return
    stop = anyio.Event()
    if loop:
        SIGNAL_HANDLERS[loop] = stop
    async with anyio.create_task_group() as tg:
        tg.start_soon(_signal_handler, stop)
        yield stop
    if loop:
        SIGNAL_HANDLERS.pop(loop, None)
