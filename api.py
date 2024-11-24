from dataclasses import dataclass
from ssl import SSLCertVerificationError
from typing import Any
import aiohttp
import asyncio
import logging
import json

from homeassistant.helpers.entity_platform import HomeAssistantError
from enum import Enum

_LOGGER = logging.getLogger(__name__)


@dataclass
class PortainerSystemStatus:
    version: str
    instance_id: str


class ContainerState(Enum):
    CREATED = "created"
    RESTARTING = "restarting"
    RUNNING = "running"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"
    REMOVING = "removing"


class PortainerContainer:
    def __init__(self, data: dict[str, Any]) -> None:
        self.snapshot_data = data

    def id(self) -> str:
        return self.snapshot_data["Id"]

    def names(self) -> list[str]:
        return self.snapshot_data["Names"]

    def name(self, i=0) -> str | None:
        names = self.names()

        if i >= len(names):
            return None

        return names[i]

    def stripped_name(self, i=0) -> str | None:
        n = self.name(i=i)

        if not n:
            return None

        return n.removeprefix("/")

    def state(self) -> ContainerState:
        return ContainerState(self.snapshot_data["State"])

    def created(self) -> int:
        return self.snapshot_data["Created"]

    def image(self) -> int:
        return self.snapshot_data["Image"]


class PortainerAPI:
    def __init__(
        self,
        host: str,
        port: str,
        api_key: str,
        ssl: bool,
        verify_ssl: bool,
        environment: int,
    ) -> None:
        self._host = host
        self._api_key = api_key
        self._ssl = ssl
        self._verify_ssl = verify_ssl
        self._environment = environment
        self._port = port
        self._session = aiohttp.ClientSession()

    async def __aenter__(self) -> "PortainerAPI":
        return self

    async def __aexit__(self, *err):
        await self.close()

    async def close(self):
        await self._session.close()
        self._session = None

    def _url(self):
        if self._ssl:
            return "https://" + self._host

        return "http://" + self._host

    async def _make_get_request(self, path: str, auth=True):
        headers = {}

        if auth:
            headers = {"X-API-Key": self._api_key}

        try:
            async with self._session.get(
                f"{self._url()}:{self._port}{path}",
                headers=headers,
                ssl=self._verify_ssl,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    res = await response.json()
                    _LOGGER.debug(json.dumps(res))
                    return res
                elif response.status == 404:
                    raise InvalidAuth
                else:
                    _LOGGER.error(
                        f'Request to "{self._url()}:{self._port}{path}" encountered a connection error.'
                    )
                    raise CannotConnect
        except SSLCertVerificationError as e:
            _LOGGER.error(
                'Request to "%s:%d%s" encountered a certificate error',
                self._url(),
                self._port,
                path,
            )

            raise SSLCertificateError
        except aiohttp.ClientConnectionError as e:
            _LOGGER.error(
                f'Request to "{self._url()}:{self._port}{path}" encountered a connection error.'
            )

            raise CannotConnect
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                'Request to "%s:%s%s" timed out', self._url(), self._port, path
            )

            _LOGGER.debug("Error details: ")
            raise CannotConnect

    async def _make_post_request_no_body(
        self, path: str, auth=True
    ) -> dict[str, any] | None:
        headers = {}

        if auth:
            headers = {"X-API-Key": self._api_key}

        try:
            async with self._session.post(
                f"{self._url()}:{self._port}{path}",
                headers=headers,
                ssl=self._verify_ssl,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    r = await response.json()
                    _LOGGER.debug(json.dumps(r))
                    return r
                elif response.status == 204 or response.status == 304:
                    return None
                elif response.status == 404:
                    raise InvalidAuth
                else:
                    _LOGGER.error(
                        f'Request to "{self._url()}:{self._port}{path}" encountered a connection error.'
                    )
                    raise CannotConnect
        except SSLCertVerificationError as e:
            _LOGGER.error(
                'Request to "%s:%d%s" encountered a certificate error',
                self._url(),
                self._port,
                path,
            )

            raise SSLCertificateError from e
        except aiohttp.ClientConnectionError as e:
            _LOGGER.error(
                f'Request to "{self._url()}:{self._port}{path}" encountered a connection error.'
            )

            raise CannotConnect from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                'Request to "%s:%s%s" timed out', self._url(), self._port, path
            )

            _LOGGER.debug("Error details: ")
            raise CannotConnect from e

    async def load_endpoints(self) -> list[dict[str, any]]:
        _LOGGER.debug("Loading Endpoints")

        return await self._make_get_request("/api/endpoints")

    async def load_endpoints_list(self) -> list[int]:
        _LOGGER.debug("Loading Endpoints List")

        endpoints = await self.load_endpoints()

        return [Endpoint(e["Id"], e["URL"], e["Name"]) for e in endpoints]

    async def system_status(self) -> PortainerSystemStatus:
        _LOGGER.debug("Fetching System Status")

        res = await self._make_get_request("/api/system/status", auth=False)

        _LOGGER.debug(json.dumps(res, indent=4))

        return PortainerSystemStatus(res["Version"], res["InstanceID"])

    async def start_container(self, endpoint_id: str, container_id: str):
        _LOGGER.debug("Issuing start request")

        await self._make_post_request_no_body(
            f"/api/endpoints/{endpoint_id}/docker/containers/{container_id}/start"
        )

    async def stop_container(self, endpoint_id: str, container_id: str):
        _LOGGER.debug("Issuing start request")

        await self._make_post_request_no_body(
            f"/api/endpoints/{endpoint_id}/docker/containers/{container_id}/stop"
        )


class Endpoint:
    def __init__(self, id: int, url: str, name: str):
        self.id = id
        self.url = url
        self.name = name

    def __str__(self) -> str:
        return f'Endpoint (id: {self.id}, url: "{self.url}", name: "{self.name}")'

    def __repr__(self) -> str:
        return f'Endpoint ({self.id}, "{self.url}", "{self.name}")'


class SSLCertificateError(HomeAssistantError):
    """Error to indicate the SSL Certifcate verification failed."""


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
