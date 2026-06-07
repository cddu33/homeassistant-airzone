"""Sensors for the Airzone Modbus integration (temperature and humidity)."""
from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from .const import DOMAIN
from .entity import AirzoneZoneEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoneSensor:
    """Description of a zone sensor."""

    key: str
    name: str
    device_class: SensorDeviceClass
    unit: str
    value_fn: Callable


# Live zone measurements, refreshed by the coordinator.
SENSORS = (
    ZoneSensor(
        "temperature",
        "Température",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        lambda entity: entity._airzone_zone.local_temperature,
    ),
    ZoneSensor(
        "humidity",
        "Humidité",
        SensorDeviceClass.HUMIDITY,
        PERCENTAGE,
        lambda entity: entity._zone_data.get("humidity"),
    ),
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        AirzoneZoneSensor(data["coordinator"], zone, description)
        for zone in data["machine"].zones
        for description in SENSORS
    ]
    async_add_entities(entities)


class AirzoneZoneSensor(AirzoneZoneEntity, SensorEntity):
    """A measured value of a zone exposed as a sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, airzone_zone, description: ZoneSensor):
        """Initialize the device."""
        super().__init__(coordinator, airzone_zone)
        self._description = description
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.unit
        self._attr_name = (
            "Airzone Zone " + str(airzone_zone._zone_id) + " " + description.name
        )
        self._attr_unique_id = f"{airzone_zone.unique_id}_{description.key}"

    @property
    def native_value(self):
        """Return the measured value."""
        return self._description.value_fn(self)
