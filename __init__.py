"""The Portainer integration."""

from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .coordinator import PortainerDataCoordinator

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

type PortainerConfigEntry = ConfigEntry[RuntimeData]  # noqa: F821


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: PortainerDataCoordinator
    cancel_update_listener: Callable


async def async_setup_entry(
    hass: HomeAssistant, config_entry: PortainerConfigEntry
) -> bool:
    """Set up Portainer from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access

    hass.data.setdefault(DOMAIN, {})

    coordinator = PortainerDataCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        raise ConfigEntryNotReady

    cancel_update_listener = config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    config_entry.runtime_data = RuntimeData(coordinator, cancel_update_listener)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle config options update.

    Reload the integration when the options change.
    Called from our listener created above.
    """
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI.

    Adding this function shows the delete device option in the UI.
    Remove this function if you do not want that option.
    You may need to do some checks here before allowing devices to be removed.
    """
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PortainerConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
