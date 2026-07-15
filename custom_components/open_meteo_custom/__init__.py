"""Support for Open-Meteo Custom."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import OpenMeteoCustomConfigEntry, OpenMeteoCustomDataUpdateCoordinator

PLATFORMS = [Platform.WEATHER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: OpenMeteoCustomConfigEntry) -> bool:
    """Set up Open-Meteo Custom from a config entry."""

    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: OpenMeteoCustomConfigEntry) -> bool:
    """Unload Open-Meteo Custom config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
