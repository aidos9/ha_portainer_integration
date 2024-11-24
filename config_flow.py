"""Config flow for Portainer integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import section

from .api import CannotConnect, Endpoint, InvalidAuth, PortainerAPI, SSLCertificateError
from .const import (
    CONNECTION_FAILED_ERROR_KEY,
    DOMAIN,
    INVALID_AUTH_ERROR_KEY,
    SSL_ERROR_KEY,
    TIMEOUT_ERROR_KEY,
    CONF_ENDPOINT_ID,
)
from .config import ConnectionConfig

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required("ssl_config"): section(
            vol.Schema(
                {
                    vol.Optional(CONF_SSL, default=True): bool,
                    vol.Optional(CONF_VERIFY_SSL, default=True): bool,
                }
            ),
            {"collapsed": False},
        ),
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def load_endpoints(hass: HomeAssistant, data: dict[str, Any]) -> list[Endpoint]:
    """Validate the user input allows us to connect and load the available endpoints.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    async with PortainerAPI(
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_API_KEY],
        data["ssl_config"][CONF_SSL],
        data["ssl_config"][CONF_VERIFY_SSL],
        0,
    ) as api:
        res = await api.load_endpoints_list()
        if not res:
            raise InvalidAuth

        return res


async def fetch_instance_id(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Validate the user input allows us to connect and load the available endpoints.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    async with PortainerAPI(
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_API_KEY],
        data["ssl_config"][CONF_SSL],
        data["ssl_config"][CONF_VERIFY_SSL],
        0,
    ) as api:
        res = await api.system_status()
        if not res:
            raise InvalidAuth

        return res.instance_id


class PortainerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Portainer."""

    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self):
        self._endpoints = []
        self._instance_id = None
        self._connection = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._endpoints = await load_endpoints(self.hass, user_input)

                instance_id = await fetch_instance_id(self.hass, user_input)

                _LOGGER.info("Setting up instance ID %s", instance_id)

                self._connection = ConnectionConfig(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_API_KEY],
                    user_input["ssl_config"][CONF_SSL],
                    user_input["ssl_config"][CONF_VERIFY_SSL],
                    instance_id,
                    None,
                )
            except SSLCertificateError:
                errors["base"] = SSL_ERROR_KEY
            except TimeoutError:
                errors["base"] = TIMEOUT_ERROR_KEY
            except CannotConnect:
                errors["base"] = CONNECTION_FAILED_ERROR_KEY
            except InvalidAuth:
                errors["base"] = INVALID_AUTH_ERROR_KEY
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self.async_step_environment()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_environment(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._connection.endpoint_id = user_input[CONF_ENDPOINT_ID]

            await self.async_set_unique_id(
                f"{self._connection.instance_id}-e{self._connection.endpoint_id}"
            )

            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Portainer ({self._connection.host}:{self._connection.port} {user_input[CONF_ENDPOINT_ID]})",
                data=self._connection.to_dict(),
            )

        return self.async_show_form(
            step_id="environment",
            last_step=True,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENDPOINT_ID): vol.In(
                        {
                            **{
                                endpoint.id: f"{endpoint.name} ({endpoint.id})"
                                for endpoint in self._endpoints
                            },
                        }
                    )
                }
            ),
        )
