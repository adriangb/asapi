from __future__ import annotations

from multiprocessing import Process, Queue
import os
import signal
import socket

import anyio
import anyio.to_thread
import pytest
from asapi import serve
from fastapi import FastAPI


async def main(logger: Queue[str], port: int) -> None:
    logger.put("start")
    app = FastAPI()
    await serve(app, port)
    logger.put("stop")


def app_subprocess(logger: Queue[str], port: int) -> None:
    anyio.run(main, logger, port)


def get_random_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@pytest.mark.anyio
async def test_serve_stop_sigint() -> None:
    q: Queue[str] = Queue(maxsize=5)
    process = Process(target=app_subprocess, args=(q, get_random_port()))
    process.start()
    assert q.get() == "start"
    # give the server enough time to actually start up
    # if not we should still shut down but there might be some errors because of task cancellation
    # and such
    await anyio.sleep(0.5)
    pid = process.pid
    assert pid is not None
    os.kill(pid, signal.SIGINT)
    with anyio.fail_after(1):
        await anyio.to_thread.run_sync(process.join)
        assert process.exitcode == 0
        r = await anyio.to_thread.run_sync(q.get)
        assert r == "stop"
