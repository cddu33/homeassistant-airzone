"""Airzone Custom Component."""
import logging

from airzone import airzone_factory
from homeassistant import config_entries, core
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_PORT

from .const import DOMAIN, PLATFORMS, SYSTEM_CLASS

_LOGGER = logging.getLogger(__name__)


def _build_machine(config):
    """Create the Airzone Modbus machine (single shared connection)."""
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    machine_id = config[CONF_DEVICE_ID]
    return airzone_factory(host, port, machine_id, SYSTEM_CLASS)


async def async_setup_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    # Build the connection once and share it across platforms (climate,
    # binary_sensor, select). A modbus bus cannot be opened twice concurrently.
    machine = await hass.async_add_executor_job(_build_machine, entry.data)

    # A single coordinator refreshes the whole machine in one modbus pass and
    # feeds every entity.
    from .coordinator import AirzoneInnobusCoordinator

    coordinator = AirzoneInnobusCoordinator(hass, machine)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "machine": machine,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry and its platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
