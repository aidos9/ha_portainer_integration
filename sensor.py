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
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from .api import ContainerState, PortainerContainer

from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PortainerConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup the sensors for each container"""

    coordinator: PortainerDataCoordinator = entry.runtime_data.coordinator

    sensors = [
        ContainerStatusSensor(coordinator, c) for c in coordinator.get_containers()
    ]

    async_add_entities(sensors)


class ContainerStatusSensor(PortainerBaseEntity, SensorEntity):
    _attr_icon = "mdi:train-car-container"

    def __init__(
        self,
        coordinator: PortainerDataCoordinator,
        container: PortainerContainer,
    ):
        super().__init__(coordinator, container, "status")

    @property
    def native_value(self) -> str | None:
        """Return the state of the entity."""
        # Using native value and native unit of measurement, allows you to change units
        # in Lovelace and HA will automatically calculate the correct value.
        return self.container.state().value

    @property
    def options(self) -> list[str]:
        return [s.value for s in ContainerState]

    @property
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.ENUM

    @property
    def name(self) -> str:
        """Return the name of the container."""
        return "status"
