# pyright: reportGeneralTypeIssues=false
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Type, TypeVar, Union, cast
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from litestar.constants import (
    HTTP_DISCONNECT,
    HTTP_RESPONSE_START,
    WEBSOCKET_CLOSE,
    WEBSOCKET_DISCONNECT,
)
from litestar.exceptions import ImproperlyConfiguredException
from litestar.serialization import decode_json, encode_json
from litestar.utils.dataclass import simple_asdict
from psycopg_pool.abc import ACT, AsyncConnectFailedCB, AsyncConnectionCB

from litestar_psycopg._utils import delete_scope_state, get_scope_state, set_scope_state

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from typing import Any

    from litestar import Litestar
    from litestar.datastructures.state import State
    from litestar.types import BeforeMessageSendHookHandler, Message, Scope


CONNECTION_SCOPE_KEY = "_psycopg_db_connection"
SESSION_TERMINUS_ASGI_EVENTS = {
    HTTP_RESPONSE_START,
    HTTP_DISCONNECT,
    WEBSOCKET_DISCONNECT,
    WEBSOCKET_CLOSE,
}
T = TypeVar("T")


async def default_before_send_handler(message: Message, scope: Scope) -> None:
    """Handle closing and cleaning up sessions before sending.

    Args:
        message: ASGI-``Message``
        scope: An ASGI-``Scope``

    Returns:
        None
    """
    session = cast(
        "Union[AsyncConnection, None]",
        get_scope_state(scope, CONNECTION_SCOPE_KEY),
    )
    if session is not None and message["type"] in SESSION_TERMINUS_ASGI_EVENTS:
        delete_scope_state(scope, CONNECTION_SCOPE_KEY)


def serializer(value: Any) -> str:
    """Serialize JSON field values.

    Args:
        value: Any json serializable value.

    Returns:
        JSON string.
    """
    return encode_json(value).decode("utf-8")


@dataclass
class AsyncConnectionPoolConfig:
    """Configuration for Psycopg's :class:`AsyncConnectionPool <psycopg_pool.AsyncConnectionPool>`.

    For details see: https://www.psycopg.org/psycopg3/docs/api/pool.html
    """

    conninfo: str
    """Connection arguments specified using as a single string in the following format: ``postgres://user:pass@host:port/database?option=value``
    """
    kwargs: Optional[Dict[str, Any]] = None
    """A dictionary of arguments which will be passed directly to the ``AsyncConnectionPool()`` as keyword arguments.
    """
    connection_class: Type[ACT] = cast(Type[ACT], AsyncConnection)
    """The class to use for connections. Must be a subclass of AsyncConnection
    """
    min_size: int = 4
    """The number of connections to keep open inside the connection pool.
    """
    max_size: Optional[int] = None
    """The max number of connections to allow in connection pool.
    """
    open: Optional[bool] = False
    """If True, open the pool, creating the required connections, on init. If False, open the pool when open() 
    is called or when the pool context is entered.
    """
    configure: Optional[AsyncConnectionCB[ACT]] = None
    """ A callback to configure a connection after creation.
    """
    check: Optional[AsyncConnectionCB[ACT]] = None
    """A callback to check that a connection is working correctly when obtained by the pool.
    """
    reset: Optional[AsyncConnectionCB[ACT]] = None
    """A callback to reset a function after it has been returned to the pool.
    """
    name: Optional[str] = None
    """An optional name to give to the pool, useful, for instance, to identify it in the logs if more than one pool is used.
    """
    timeout: float = 30.0
    """The default maximum time in seconds that a client can wait to receive a connection from the pool.
    """
    max_waiting: int = 0
    """Maximum number of requests that can be queued to the pool, after which new requests will fail, raising TooManyRequests. 0 means no queue limit.
    """
    max_lifetime: float = 60 * 60.0
    """The maximum lifetime of a connection in the pool, in seconds.
    """
    max_idle: float = 10 * 60.0
    """Maximum time, in seconds, that a connection can stay unused in the pool before being closed, and the pool shrunk.
    """
    reconnect_timeout: float = 5 * 60.0
    """Maximum time, in seconds, the pool will try to create a connection.
    """
    reconnect_failed: Optional[AsyncConnectFailedCB] = None
    """Callback invoked if an attempt to create a new connection fails for more than reconnect_timeout seconds.
    """
    num_workers: int = 3
    """Number of background worker threads used to maintain the pool state.
    """


@dataclass
class PsycopgConfig:
    """Psycopg Configuration."""

    pool_config: AsyncConnectionPoolConfig | None = None
    """Psycopg AsyncConnectionPool configuration"""
    pool_app_state_key: str = "db_pool"
    """Key under which to store the pscopg pool in the application :class:`State <.datastructures.State>`
    instance.
    """
    pool_dependency_key: str = "db_pool"
    """Key under which to store the pscopg AsyncConnectionPool in the application dependency injection map.    """
    connection_dependency_key: str = "db_connection"
    """Key under which to store the Psycopg AsyncConnectionPool in the application dependency injection map.    """
    before_send_handler: BeforeMessageSendHookHandler = default_before_send_handler
    """Handler to call before the ASGI message is sent.

    The handler should handle closing the session stored in the ASGI scope, if it's still open, and committing and
    uncommitted data.
    """
    json_deserializer: Callable[[str], Any] = decode_json
    """For dialects that support the :class:`JSON <sqlalchemy.types.JSON>` datatype, this is a Python callable that will
    convert a JSON string to a Python object. By default, this is set to Litestar's
    :attr:`decode_json() <.serialization.decode_json>` function."""
    json_serializer: Callable[[Any], str] = serializer
    """For dialects that support the JSON datatype, this is a Python callable that will render a given object as JSON.
    By default, Litestar's :attr:`encode_json() <.serialization.encode_json>` is used."""
    pool_instance: AsyncConnectionPool | None = None
    """Optional pool to use.

    If set, the plugin will use the provided pool rather than instantiate one.
    """

    @property
    def pool_config_dict(self) -> dict[str, Any]:
        """Return the pool configuration as a dict.

        Returns:
            A string keyed dict of config kwargs for the Psycopg :func:`create_pool <psycopg.pool.create_pool>`
            function.
        """
        if self.pool_config:
            return simple_asdict(
                self.pool_config, exclude_empty=True, convert_nested=False
            )
        msg = (
            "'pool_config' methods can not be used when a 'pool_instance' is provided."
        )
        raise ImproperlyConfiguredException(msg)

    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {
            "AsyncConnection": AsyncConnection,
            "AsyncConnectionPool": AsyncConnectionPool,
        }

    async def create_pool(self) -> AsyncConnectionPool:
        """Return a pool. If none exists yet, create one.

        Returns:
            Getter that returns the pool instance used by the plugin.
        """
        if self.pool_instance is not None:
            return self.pool_instance

        if self.pool_config is None:
            msg = "One of 'pool_config' or 'pool_instance' must be provided."
            raise ImproperlyConfiguredException(msg)

        pool_config = self.pool_config_dict
        self.pool_instance = AsyncConnectionPool(**pool_config)
        if self.pool_instance is None:
            msg = "Could not configure the 'pool_instance'. Please check your configuration."
            raise ImproperlyConfiguredException(msg)
        await self.pool_instance.open()
        await self.pool_instance.wait()
        return self.pool_instance

    @asynccontextmanager
    async def lifespan(
        self,
        app: Litestar,
    ) -> AsyncGenerator[None, None]:
        db_pool = await self.create_pool()
        app.state.update({self.pool_app_state_key: db_pool})
        try:
            yield
        finally:
            await db_pool.close()

    def provide_pool(self, state: State) -> AsyncConnectionPool:
        """Create a pool instance.

        Args:
            state: The ``Litestar.state`` instance.

        Returns:
            A AsyncConnectionPool instance.
        """
        return cast("AsyncConnectionPool", state.get(self.pool_app_state_key))

    async def provide_connection(
        self,
        state: State,
        scope: Scope,
    ) -> AsyncGenerator[AsyncConnection, None]:
        """Create a connection instance.

        Args:
            state: The ``Litestar.state`` instance.
            scope: The current connection's scope.

        Returns:
            A connection instance.
        """
        connection = cast(
            "Optional[AsyncConnection]",
            get_scope_state(scope, CONNECTION_SCOPE_KEY),
        )
        if connection is None:
            pool = cast("AsyncConnectionPool", state.get(self.pool_app_state_key))

            async with pool.connection() as connection:
                set_scope_state(scope, CONNECTION_SCOPE_KEY, connection)
                yield connection

    @asynccontextmanager
    async def get_connection(
        self,
    ) -> AsyncGenerator[AsyncConnection, None]:
        """Create a connection instance.

        Args:
            pool: The pool to grab a connection from

        Returns:
            A connection instance.
        """
        async with (await self.create_pool()).connection() as connection:
            yield connection
