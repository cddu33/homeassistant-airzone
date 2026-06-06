"""Airzone Custom Component."""
import logging

from airzone import airzone_factory
from homeassistant import config_entries, core
from homeassistant.const import CONF_DEVICE_CLASS, CONF_DEVICE_ID, CONF_HOST, CONF_PORT

from .const import CONF_SPEED_PERCENTAGE, DEFAULT_SPEED_AS_PER, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


def _build_machine(config):
    """Create the Airzone machine (single shared connection)."""
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    machine_id = config[CONF_DEVICE_ID]
    system_class = config[CONF_DEVICE_CLASS]
    aidoo_args = {"speed_as_per": config.get(CONF_SPEED_PERCENTAGE, DEFAULT_SPEED_AS_PER)}
    return airzone_factory(host, port, machine_id, system_class, **aidoo_args)


async def async_setup_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    # Build the connection once and share it across platforms (climate,
    # binary_sensor). A modbus RTU bus cannot be opened twice concurrently.
    machine = await hass.async_add_executor_job(_build_machine, entry.data)
    hass.data[DOMAIN][entry.entry_id] = {"config": entry.data, "machine": machine}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
