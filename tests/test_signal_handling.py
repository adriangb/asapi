from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
import os
from pathlib import Path
import signal
import socket
import sys
from tempfile import TemporaryDirectory
from typing import AsyncIterator

import anyio
import anyio.abc
import anyio.to_thread
import httpx
import pytest


def get_random_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@asynccontextmanager
async def cleanup_process(process: anyio.abc.Process) -> AsyncIterator[None]:
    try:
        yield
    except Exception as e:
        print(e)
        raise
    finally:
        if process.returncode is not None:
            return
        process.kill()
        await process.wait()


async def wait_for_server(port: int) -> None:
    async with httpx.AsyncClient() as client:
        while True:
            await anyio.sleep(0.05)
            try:
                resp = await client.get(f"http://localhost:{port}/docs")
                if resp.status_code == 200:
                    break
            except httpx.NetworkError:
                pass


@pytest.mark.anyio
async def test_serve_stop_sigint() -> None:
    port = get_random_port()

    async with AsyncExitStack() as stack:
        td = stack.enter_context(TemporaryDirectory())

        file = os.path.join(td, "log.txt")
        program = str((Path(__file__).parent / "run_server.py").resolve().absolute())
        command = [sys.executable, program, file, str(port)]

        process = await stack.enter_async_context(
            await anyio.open_process(command, start_new_session=True)
        )
        await stack.enter_async_context(cleanup_process(process))
        # wait for the server to start
        with anyio.fail_after(5):
            await wait_for_server(port)

        process.send_signal(signal.SIGINT)
        with anyio.fail_after(5):
            code = await process.wait()
            assert code == 0

        with open(file) as f:
            assert f.read().split("\n") == ["start", "stop"]
