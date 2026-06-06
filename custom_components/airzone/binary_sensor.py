"""Binary sensors for the Airzone integration."""
import logging

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone binary sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]

    # The low battery flag is only exposed by Innobus (modbus) zones.
    if data["config"][CONF_DEVICE_CLASS] != "innobus":
        return

    coordinator = data["coordinator"]
    entities = [
        AirzoneZoneBatterySensor(coordinator, zone)
        for zone in data["machine"].zones
    ]
    async_add_entities(entities)


class AirzoneZoneBatterySensor(CoordinatorEntity, BinarySensorEntity):
    """Low battery flag of an Innobus (Lite Radio) zone thermostat."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, coordinator, airzone_zone):
        """Initialize the device."""
        super().__init__(coordinator)
        self._airzone_zone = airzone_zone
        self._attr_name = "Airzone Zone " + str(airzone_zone._zone_id) + " Battery"
        self._attr_unique_id = f"{airzone_zone.unique_id}_battery"

    @property
    def device_info(self) -> DeviceInfo:
        """Attach to the same device as the zone climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._airzone_zone.unique_id)},
            via_device=(DOMAIN, self._airzone_zone._machine.unique_id),
        )

    @property
    def is_on(self):
        """Return True when the zone thermostat reports a low battery."""
        zone = self.coordinator.data["zones"].get(self._airzone_zone.unique_id, {})
        return zone.get("low_battery")
