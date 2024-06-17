import sys
import anyio
from fastapi import FastAPI

from asapi import serve


async def main(log_file: str, port: int) -> None:
    with open(log_file, "w") as f:
        f.write("start")
        app = FastAPI()
        await serve(app, port)
        f.write("\nstop")


if __name__ == "__main__":
    file = sys.argv[1]
    port = int(sys.argv[2])
    anyio.run(main, file, port)
