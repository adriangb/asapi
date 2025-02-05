from __future__ import annotations

import signal
import types
from asyncio import CancelledError
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

import anyio


@dataclass
class SignalHandler:
    stop: anyio.Event
    previous: Callable[[int, types.FrameType | None], Any] | None

    def handle(self, signum: int, frame: types.FrameType | None) -> None:
        self.stop.set()
        if self.previous is not None:
            self.previous(signum, frame)


@asynccontextmanager
async def handle_signals() -> AsyncIterator[anyio.Event]:
    """Handle SIGTERM and SIGINT signals.

    This context manager provides an anyio Event that gets set when a signal is received and we are shutting down.
    """
    stop = anyio.Event()
    sigterm_handler = SignalHandler(stop, None)
    previous_sigterm_handler = signal.signal(signal.SIGTERM, sigterm_handler.handle)
    if previous_sigterm_handler is not None and not isinstance(
        previous_sigterm_handler, int
    ):
        sigterm_handler.previous = previous_sigterm_handler
    sigint_handler = SignalHandler(stop, None)
    previous_sigint_handler = signal.signal(signal.SIGINT, sigint_handler.handle)
    if previous_sigint_handler is not None and not isinstance(
        previous_sigint_handler, int
    ):
        sigint_handler.previous = previous_sigint_handler
    try:
        yield stop
    except (KeyboardInterrupt, CancelledError):
        pass
    finally:
        stop.set()
        if sigterm_handler.previous is not None:
            signal.signal(signal.SIGTERM, sigterm_handler.previous)
        if sigint_handler.previous is not None:
            signal.signal(signal.SIGINT, sigint_handler.previous)
