"""Switch entities for the Airzone Modbus integration (zone settings bits)."""
from dataclasses import dataclass
import logging

from homeassistant import config_entries, core
from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, ZONE_REGISTER_SETTINGS, ZONE_REGISTER_WATER
from .entity import AirzoneZoneEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoneSwitch:
    """Description of a bit-based zone switch."""

    key: str
    name: str
    register: int
    bit: int
    icon: str = None


# Writable zone settings bits (Airzone Modbus map, registers 4 and 22).
SWITCHES = (
    ZoneSwitch("heating_air", "Air Heating", ZONE_REGISTER_SETTINGS, 2, "mdi:fire"),
    ZoneSwitch("floor_heating", "Floor Heating", ZONE_REGISTER_SETTINGS, 3, "mdi:heating-coil"),
    ZoneSwitch("antifreeze", "Antifreeze", ZONE_REGISTER_SETTINGS, 4, "mdi:snowflake-alert"),
    ZoneSwitch("air_cooling", "Air Cooling", ZONE_REGISTER_WATER, 0, "mdi:snowflake"),
    ZoneSwitch("floor_cooling", "Floor Cooling", ZONE_REGISTER_WATER, 1, "mdi:snowflake-thermometer"),
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone switches from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        AirzoneZoneSwitch(data["coordinator"], zone, description)
        for zone in data["machine"].zones
        for description in SWITCHES
    ]
    async_add_entities(entities)


class AirzoneZoneSwitch(AirzoneZoneEntity, SwitchEntity):
    """A single writable bit of a zone register exposed as a switch."""

    def __init__(self, coordinator, airzone_zone, description: ZoneSwitch):
        """Initialize the device."""
        super().__init__(coordinator, airzone_zone)
        self._description = description
        self._attr_icon = description.icon
        self._attr_name = (
            "Airzone Zone " + str(airzone_zone._zone_id) + " " + description.name
        )
        self._attr_unique_id = f"{airzone_zone.unique_id}_{description.key}"

    @property
    def is_on(self):
        """Return the state of the configured register bit."""
        register = self._register(self._description.register)
        if register is None:
            return None
        return bool(register & (1 << self._description.bit))

    def turn_on(self, **kwargs) -> None:
        """Set the register bit."""
        self._write_bit(self._description.register, self._description.bit, True)

    def turn_off(self, **kwargs) -> None:
        """Clear the register bit."""
        self._write_bit(self._description.register, self._description.bit, False)
