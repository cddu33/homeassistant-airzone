"""Binary sensors for the Airzone integration."""
import logging

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, ZONE_LOW_BATTERY_BIT, ZONE_REGISTER_ERRORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone binary sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    config = data["config"]
    machine = data["machine"]

    # The low battery flag is only exposed by Innobus (modbus) zones.
    if config[CONF_DEVICE_CLASS] != "innobus":
        return

    entities = [AirzoneZoneBatterySensor(zone) for zone in machine.zones]
    async_add_entities(entities, update_before_add=True)


class AirzoneZoneBatterySensor(BinarySensorEntity):
    """Low battery flag of an Innobus (Lite Radio) zone thermostat."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, airzone_zone):
        """Initialize the device."""
        self._airzone_zone = airzone_zone
        self._attr_name = "Airzone Zone " + str(airzone_zone._zone_id) + " Battery"
        self._attr_unique_id = f"{airzone_zone.unique_id}_battery"
        self._attr_is_on = None

    @property
    def device_info(self) -> DeviceInfo:
        """Attach to the same device as the zone climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._airzone_zone.unique_id)},
            via_device=(DOMAIN, self._airzone_zone._machine.unique_id),
        )

    def update(self):
        """Read the zone errors register and extract the low battery bit."""
        # The low battery flag is bit 8 of zone register 13 ("Zone errors"),
        # which the library does not fetch (it only reads registers 0-12).
        try:
            register = self._airzone_zone._machine.read_registers(
                self._airzone_zone.base_zone + ZONE_REGISTER_ERRORS, 1
            )[0]
            self._attr_is_on = bool(register & (1 << ZONE_LOW_BATTERY_BIT))
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Could not read zone errors register (%s): %s",
                ZONE_REGISTER_ERRORS,
                err,
            )
            self._attr_is_on = None
