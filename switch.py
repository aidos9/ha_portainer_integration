""""""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from . import PortainerConfigEntry
from .coordinator import PortainerDataCoordinator
from .const import DOMAIN
from .base import PortainerBaseEntity
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from .api import ContainerState, PortainerContainer

from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PortainerConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup the switches for each container"""

    coordinator: PortainerDataCoordinator = entry.runtime_data.coordinator

    switches = [
        ContainerRunningSwitch(coordinator, c) for c in coordinator.get_containers()
    ]

    async_add_entities(switches)


class ContainerRunningSwitch(PortainerBaseEntity, SwitchEntity):
    _attr_icon = "mdi:toggle-switch-variant-off"

    def __init__(
        self,
        coordinator: PortainerDataCoordinator,
        container: PortainerContainer,
    ):
        super().__init__(coordinator, container, "running-switch")

    @property
    def is_on(self) -> bool:
        """Return the state of the entity."""

        return self.container.state() in [
            ContainerState.RUNNING,
            ContainerState.RESTARTING,
        ]

    @property
    def name(self) -> str:
        """Return the name of the container."""
        return "start"

    async def async_turn_on(self):
        _LOGGER.info("Turning on container %s", self.container.stripped_name())

        await self.coordinator.start_container(self.container_id)

        await asyncio.sleep(5)

        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        _LOGGER.info("Turning off container %s", self.container.stripped_name())

        await self.coordinator.stop_container(self.container_id)

        await asyncio.sleep(5)

        await self.coordinator.async_refresh()

    @property
    def device_class(self) -> SwitchDeviceClass:
        return SwitchDeviceClass.SWITCH
