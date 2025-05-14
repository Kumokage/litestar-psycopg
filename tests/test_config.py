import pytest
from pytest_databases.docker.postgres import PostgresService

from litestar_psycopg import AsyncConnectionPoolConfig, PsycopgConfig

pytestmark = pytest.mark.anyio


async def test_get_connection(postgres_service: PostgresService) -> None:
    psycopg_config = PsycopgConfig(
        pool_config=AsyncConnectionPoolConfig(
            conninfo=f"postgresql://{postgres_service.user}:{postgres_service.password}@{postgres_service.host}:{postgres_service.port}/{postgres_service.database}"
        )
    )

    async with psycopg_config.get_connection() as db_connection:
        cursor = await db_connection.execute("select 1 as one")
        r = await cursor.fetchone()
        assert r is not None
        assert r[0] == 1
