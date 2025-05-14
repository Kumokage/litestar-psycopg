from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from litestar.di import Provide
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

    from litestar_psycopg.config import PsycopgConfig


class SlotsBase:
    __slots__ = ("_config",)


class PsycopgPlugin(InitPluginProtocol, SlotsBase):
    """Psycopg plugin."""

    __slots__ = ()

    def __init__(self, config: PsycopgConfig) -> None:
        """Initialize ``PsycopgPlugin``.

        Args:
            config: configure and start Psycopg pool.
        """
        self._config = config

    @property
    def config(self) -> PsycopgConfig:
        """Return the plugin config.

        Returns:
            PsycopgConfig.
        """
        return self._config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with Psycopg pool.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """

        app_config.dependencies.update(
            {
                self._config.pool_dependency_key: Provide(
                    self._config.provide_pool, sync_to_thread=False
                ),
                self._config.connection_dependency_key: Provide(
                    self._config.provide_connection
                ),
            },
        )
        app_config.type_encoders = {
            uuid.UUID: str,
            **(app_config.type_encoders or {}),
        }
        app_config.before_send.append(self._config.before_send_handler)
        app_config.lifespan.append(self._config.lifespan)
        app_config.signature_namespace.update(self._config.signature_namespace)

        return app_config
