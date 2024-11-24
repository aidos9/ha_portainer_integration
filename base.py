from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import PortainerDataCoordinator
from .api import PortainerContainer, ContainerState
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

from typing import Any
import logging

_LOGGER = logging.getLogger(__name__)


class PortainerBaseEntity(CoordinatorEntity):
    coordinator: PortainerDataCoordinator

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PortainerDataCoordinator,
        container: PortainerContainer,
        id_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self.container = container
        self.container_id = container.id()
        self.id_suffix = id_suffix

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.container = self.coordinator.get_container(self.container_id)

        _LOGGER.debug(
            "Updating device: %s, %s",
            self.container_id,
            self.container.name(),
        )

        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """"""
        return DeviceInfo(
            name=self.container.name().removeprefix("/"),
            created_at=self.container.created(),
            identifiers={(DOMAIN, self.container_id)},
        )

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-{self.container_id}-{self.id_suffix}"
