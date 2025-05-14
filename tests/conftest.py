from __future__ import annotations

from pathlib import Path

import pytest
from examples.base import SampleController
from litestar import Litestar
from psycopg_pool import AsyncConnectionPool

from litestar_psycopg import PsycopgConfig, PsycopgPlugin

here = Path(__file__).parent


pytestmark = pytest.mark.anyio
pytest_plugins = [
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(name="connection_pool", scope="session")
async def connection_pool(
    postgres_docker_ip: str,
    postgres_user: str,
    postgres_password: str,
    postgres_database: str,
    postgres_port: int,
    postgres_service: None,
) -> AsyncConnectionPool:
    """App fixture.

    Returns:
        An application instance, configured via plugin.
    """
    return AsyncConnectionPool(
        conninfo=f"postgresql://{postgres_user}:{postgres_password}@{postgres_docker_ip}:{postgres_port}/{postgres_database}",
        min_size=1,
        max_size=1,
    )


@pytest.fixture(name="plugin")
async def plugin(connection_pool: AsyncConnectionPool) -> PsycopgPlugin:
    """App fixture.

    Returns:
        An application instance, configured via plugin.
    """

    return PsycopgPlugin(
        config=PsycopgConfig(
            pool_instance=connection_pool,
        ),
    )


@pytest.fixture(name="app")
def fx_app(plugin: PsycopgPlugin) -> Litestar:
    """App fixture.

    Returns:
        An application instance, configured via plugin.
    """
    return Litestar(plugins=[plugin], route_handlers=[SampleController])
