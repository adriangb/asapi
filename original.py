from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator
from fastapi import FastAPI, Depends
from psycopg_pool import AsyncConnectionPool
import uvicorn


@asynccontextmanager
async def create_pool() -> AsyncIterator[AsyncConnectionPool]:
    async with AsyncConnectionPool(
        "postgres://postgres:postgres@localhost:5432/postgres"
    ) as pool:
        yield pool


app = FastAPI()


@app.get("/hello/{name}")
async def hello(
    name: str, pool: Annotated[AsyncConnectionPool, Depends(create_pool)]
) -> str:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT '¡Hola ' || %(name)s || '!'", {"name": name})
            res = await cur.fetchone()
            assert res is not None
            return res[0]


if __name__ == "__main__":
    uvicorn.run(app)
