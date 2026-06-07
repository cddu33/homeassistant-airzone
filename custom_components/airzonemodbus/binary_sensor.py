"""Binary sensors for the Airzone Modbus integration."""
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Optional

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .const import (
    DOMAIN,
    ZONE_LOW_BATTERY_BIT,
    ZONE_REGISTER_ERRORS,
    ZONE_REGISTER_STATE,
)
from .entity import AirzoneZoneEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoneBinarySensor:
    """Description of a bit-based zone binary sensor."""

    key: str
    name: str
    register: int
    bit: int
    device_class: Optional[BinarySensorDeviceClass] = None
    # Returns True if the sensor is relevant for a given zone (capability).
    available_fn: Optional[Callable] = None


def _relay_configured(getter):
    """True if a presence/window relay is configured (not OFF)."""
    from airzone.innobus import RelayConfig

    return getter() != RelayConfig.OFF


# Read-only zone states, per the Airzone Modbus map (registers 9 and 13).
BINARY_SENSORS = (
    ZoneBinarySensor("battery", "Pile", ZONE_REGISTER_ERRORS, ZONE_LOW_BATTERY_BIT,
                     BinarySensorDeviceClass.BATTERY),
    ZoneBinarySensor("air_demand", "Demande air", ZONE_REGISTER_STATE, 7,
                     BinarySensorDeviceClass.RUNNING,
                     available_fn=lambda z: z.is_AA_enabled()),
    ZoneBinarySensor("radiant_demand", "Demande sol", ZONE_REGISTER_STATE, 5,
                     BinarySensorDeviceClass.RUNNING,
                     available_fn=lambda z: z.is_Floor_enabled()),
    ZoneBinarySensor("presence", "Présence", ZONE_REGISTER_STATE, 8,
                     BinarySensorDeviceClass.OCCUPANCY,
                     available_fn=lambda z: _relay_configured(z.get_presence)),
    ZoneBinarySensor("window", "Fenêtre", ZONE_REGISTER_STATE, 9,
                     BinarySensorDeviceClass.WINDOW,
                     available_fn=lambda z: _relay_configured(z.get_window)),
)


def _is_relevant(zone, description: ZoneBinarySensor) -> bool:
    """Whether a sensor applies to this zone; default to exposing it."""
    if description.available_fn is None:
        return True
    try:
        return bool(description.available_fn(zone))
    except Exception:  # noqa: BLE001
        return True


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone binary sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        AirzoneZoneBinarySensor(data["coordinator"], zone, description)
        for zone in data["machine"].zones
        for description in BINARY_SENSORS
        if _is_relevant(zone, description)
    ]
    async_add_entities(entities)


class AirzoneZoneBinarySensor(AirzoneZoneEntity, BinarySensorEntity):
    """A single bit of a zone register exposed as a binary sensor."""

    def __init__(self, coordinator, airzone_zone, description: ZoneBinarySensor):
        """Initialize the device."""
        super().__init__(coordinator, airzone_zone)
        self._description = description
        self._attr_device_class = description.device_class
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
