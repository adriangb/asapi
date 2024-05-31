# asapi

A thin opinionated wrapper around FastAPI. Because it's wrapping FastAPI you can work it into your existing projects.

## Explicit composition root

FastAPI uses callbacks inside of `Depends` to do it's dependency injection.
This forces you to end up using multiple layers of `Depends` to compose your application.
The creation of these `Depends` resources often ends up distributed across modules so it's hard to know where something is initialized.

FastAPI also has no application-level dependencies, so you end up having to use globals to share resources across requests.

`asapi` solves this by having an explicit composition root where you can define all your dependencies in one place.

Endpoints then use `Injected[DependencyType]` to get access to the dependencies they need.

## Example

```python
import anyio
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from asapi import FromPath, Injected, serve, bind


app = FastAPI()


@app.get("/hello/{name}")
async def hello(
    name: FromPath[str],
    pool: Injected[AsyncConnectionPool],
) -> str:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT '¡Hola ' || %(name)s || '!'", {"name": name})
            res = await cur.fetchone()
            assert res is not None
            return res[0]
```

TODO: in the future I'd like to provide a wrapper around `APIRouter` and `FastAPI` that also forces you to mark every argument to an endpoint as `Injected`, `Query`, `Path`, `Body`, which makes it explicit where arguments are coming from with minimal boilerplate.

## Run in your event loop

FastAPI recommends using Uvicorn to run your application (note: if you're using Gunicorn you probably don't need to unless you're deploying on a a 'bare meta' server with multiple cores like a large EC2 instance).

But using `uvicorn app:app` from the command line has several issues:

1. It takes control of the event loop and startup out of your hands. You have to rely on Uvicorn to configure the event loop, configure logging, etc.
2. You'll have to use ASGI lifespans to initialize your resources, or the globals trick mentioned above.
3. You can't run anything else in the event loop (e.g. a background worker).

`asapi` solves this by providing a `serve` function that you can use to run your application in your own event loop.

```python
import anyio
from asapi import serve
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


async def main():
    await serve(app, 8000)

if __name__ == "__main__":
    anyio.run(main)
```

Now you have full control of the event loop and can make database connections, run background tasks, etc.
Combined with the explicit composition root, you can initialize all your resources in one place:

```python
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
```
