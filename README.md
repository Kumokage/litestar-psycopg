# Litestar Psycopg

[![codecov](https://codecov.io/gh/Kumokage/litestar-psycopg/graph/badge.svg?token=906N4AE4KH)](https://codecov.io/gh/Kumokage/litestar-psycopg) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Kumokage_litestar-psycopg&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Kumokage_litestar-psycopg) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=Kumokage_litestar-psycopg&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=Kumokage_litestar-psycopg) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=Kumokage_litestar-psycopg&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=Kumokage_litestar-psycopg) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=Kumokage_litestar-psycopg&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=Kumokage_litestar-psycopg) [![PyPI - Version](https://img.shields.io/pypi/v/litestar-psycopg?labelColor=202235&color=edb641&logo=python&logoColor=edb641)](https://badge.fury.io/py/litestar-psycopg) ![PyPI - Support Python Versions](https://img.shields.io/pypi/pyversions/litestar-psycopg?labelColor=202235&color=edb641&logo=python&logoColor=edb641) [![PyPI Downloads](https://static.pepy.tech/badge/litestar-psycopg)](https://pepy.tech/projects/litestar-psycopg) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json&labelColor=202235)](https://github.com/astral-sh/ruff)

Infrastructure Litestar pluging for data access throw Psycopg. This plugin is useful for when you plan to use no ORM or need to manage the postgres connection separately.

## Usage

### Installation

```shell
pip install litestar-psycopg
```

### Example

Here is a basic application that demonstrates how to use the plugin.

```python
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
```
