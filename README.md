# Litestar Psycopg

[![PyPI - Version](https://img.shields.io/pypi/v/litestar-psycopg?labelColor=202235&color=edb641&logo=python&logoColor=edb641)](https://badge.fury.io/py/litestar-psycopg) ![PyPI - Support Python Versions](https://img.shields.io/pypi/pyversions/litestar-psycopg?labelColor=202235&color=edb641&logo=python&logoColor=edb641) ![litestar-psycopg PyPI - Downloads](https://img.shields.io/pypi/dm/litestar-psycopg?logo=python&label=package%20downloads&labelColor=202235&color=edb641&logoColor=edb641) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json&labelColor=202235)](https://github.com/astral-sh/ruff)
A barebones Psycopg plugin for Litestar. This plugin is useful for when you plan to use no ORM or need to manage the postgres connection separately.

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
