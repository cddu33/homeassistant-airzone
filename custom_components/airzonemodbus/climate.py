import logging

from homeassistant import config_entries, core

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the climate entities from a config entry."""
    from .innobus import InnobusMachine, InnobusZone

    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    machine = data["machine"]

    entities = [InnobusMachine(coordinator, machine)]
    entities += [InnobusZone(coordinator, zone) for zone in machine.zones]
    async_add_entities(entities)
