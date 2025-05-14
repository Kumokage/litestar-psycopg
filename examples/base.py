from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec
from litestar import Controller, Litestar, get
from litestar.exceptions import InternalServerException

from litestar_psycopg import PsycopgConfig, PsycopgPlugin, AsyncConnectionPoolConfig

if TYPE_CHECKING:
    from psycopg import AsyncConnection


class PostgresHealthCheck(msgspec.Struct):
    """A new type describing a User"""

    version: str
    uptime: float


class SampleController(Controller):
    @get(path="/sample")
    async def sample_route(self, db_connection: AsyncConnection) -> PostgresHealthCheck:
        """Check database available and returns app config info."""
        cursor = await db_connection.execute(
            "select version() as version, extract(epoch from current_timestamp - pg_postmaster_start_time()) as uptime",
        )
        result = await cursor.fetchone()
        if result:
            return PostgresHealthCheck(version=result[0], uptime=result[1])
        raise InternalServerException


psycopg = PsycopgPlugin(
    config=PsycopgConfig(
        pool_config=AsyncConnectionPoolConfig(
            conninfo="postgresql://app:app@localhost:5432/app"
        )
    )
)
app = Litestar(plugins=[psycopg], route_handlers=[SampleController])
