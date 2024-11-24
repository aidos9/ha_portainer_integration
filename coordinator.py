from datetime import timedelta
import logging
from typing import Any
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    CannotConnect,
    InvalidAuth,
    PortainerAPI,
    SSLCertificateError,
    PortainerContainer,
)
from .const import (
    CONNECTION_FAILED_ERROR_KEY,
    INVALID_AUTH_ERROR_KEY,
    SSL_ERROR_KEY,
    TIMEOUT_ERROR_KEY,
    CONF_ENDPOINT_ID,
)

_LOGGER = logging.getLogger(__name__)


class PortainerDataCoordinator(DataUpdateCoordinator):
    data: dict[str, any]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=3),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )

        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.api_key = config_entry.data[CONF_API_KEY]
        self.ssl = config_entry.data[CONF_SSL]
        self.verify_ssl = config_entry.data[CONF_VERIFY_SSL]
        self.environment = config_entry.data[CONF_ENDPOINT_ID]

        self.api = PortainerAPI(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            ssl=self.ssl,
            verify_ssl=self.verify_ssl,
            environment=self.environment,
        )

    async def _async_update_data(self):
        try:
            data = list(
                filter(
                    lambda e: e["Id"] == self.environment,
                    await self.api.load_endpoints(),
                )
            )[0]
        except SSLCertificateError as err:
            _LOGGER.error("SSL Certificate Failed")
            # errors["base"] = SSL_ERROR_KEY
            raise UpdateFailed("") from err
        except TimeoutError as err:
            _LOGGER.error("Server Connection Timed Out")
            # errors["base"] = TIMEOUT_ERROR_KEY
        except CannotConnect:
            _LOGGER.error("Failed to connect to the server")
            # errors["base"] = CONNECTION_FAILED_ERROR_KEY
        except InvalidAuth:
            _LOGGER.error("Server authentication was invalid")
            # errors["base"] = INVALID_AUTH_ERROR_KEY
        except Exception as err:
            _LOGGER.error(f"Unexpected exception: {err}")
            # errors["base"] = "unknown"
            raise UpdateFailed(
                f"Error communicating with Portainer API: {err}"
            ) from err
        else:
            _LOGGER.debug(json.dumps(data))
            return data

    def get_containers(self) -> list[PortainerContainer]:
        return [
            PortainerContainer(c)
            for c in self.data["Snapshots"][0]["DockerSnapshotRaw"]["Containers"]
        ]

    def get_container(self, container_id: str) -> PortainerContainer:
        for container in self.get_containers():
            if container.id() == container_id:
                return container

        return None

    async def start_container(self, container_id: str):
        await self.api.start_container(self.environment, container_id)

    async def stop_container(self, container_id: str):
        await self.api.stop_container(self.environment, container_id)
