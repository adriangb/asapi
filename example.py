import anyio
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from asapi import FromPath, Injected, serve, bind


app = FastAPI()


@app.get("/hello/{name}")
async def hello(name: FromPath[str], pool: Injected[AsyncConnectionPool]) -> str:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT '¡Hola ' || %(name)s || '!'", {"name": name})
            res = await cur.fetchone()
            assert res is not None
            return res[0]


async def main() -> None:
    async with AsyncConnectionPool(
        "postgres://postgres:postgres@localhost:5432/postgres"
    ) as pool:
        bind(app, AsyncConnectionPool, pool)
        await serve(app, 8000)


if __name__ == "__main__":
    anyio.run(main)
