"""Select entities for the Airzone integration (zone sleep timer)."""
import logging

from homeassistant import config_entries, core
from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SLEEP_OPTIONS

_LOGGER = logging.getLogger(__name__)

# Zone register 0 holds the operation mode; bits 6-7 are the sleep level.
ZONE_REGISTER_MODE = 0
ZONE_SLEEP_BIT_OFFSET = 6
ZONE_SLEEP_MASK = 0b11 << ZONE_SLEEP_BIT_OFFSET


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone select entities from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]

    # The sleep timer is only exposed by Innobus (modbus) zones.
    if data["config"][CONF_DEVICE_CLASS] != "innobus":
        return

    coordinator = data["coordinator"]
    entities = [
        AirzoneZoneSleepSelect(coordinator, zone)
        for zone in data["machine"].zones
    ]
    async_add_entities(entities)


class AirzoneZoneSleepSelect(CoordinatorEntity, SelectEntity):
    """Sleep timer (Off / 30 / 60 / 90 minutes) of an Innobus zone."""

    _attr_options = SLEEP_OPTIONS
    _attr_icon = "mdi:power-sleep"

    def __init__(self, coordinator, airzone_zone):
        """Initialize the device."""
        super().__init__(coordinator)
        self._airzone_zone = airzone_zone
        self._attr_name = "Airzone Zone " + str(airzone_zone._zone_id) + " Sleep"
        self._attr_unique_id = f"{airzone_zone.unique_id}_sleep"

    @property
    def device_info(self) -> DeviceInfo:
        """Attach to the same device as the zone climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._airzone_zone.unique_id)},
            via_device=(DOMAIN, self._airzone_zone._machine.unique_id),
        )

    @property
    def current_option(self):
        """Return the current sleep level provided by the coordinator."""
        zone = self.coordinator.data["zones"].get(self._airzone_zone.unique_id, {})
        level = zone.get("sleep")
        if level is None or level >= len(SLEEP_OPTIONS):
            return None
        return SLEEP_OPTIONS[level]

    def select_option(self, option: str) -> None:
        """Write the sleep level into bits 6-7 of zone register 0."""
        level = SLEEP_OPTIONS.index(option)
        current = self._airzone_zone.zone_state[ZONE_REGISTER_MODE]
        new_value = (current & ~ZONE_SLEEP_MASK) | (level << ZONE_SLEEP_BIT_OFFSET)
        self._airzone_zone.write_register(ZONE_REGISTER_MODE, new_value)
