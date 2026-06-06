"""DataUpdateCoordinator for the Airzone Innobus (modbus) system."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ZONE_LOW_BATTERY_BIT, ZONE_REGISTER_ERRORS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

# System registers holding the global set-point min/max limits.
SYSTEM_REGISTER_MIN_SETPOINT = 25
SYSTEM_REGISTER_MAX_SETPOINT = 26
# Per-zone register holding the humidity value (0-100).
ZONE_REGISTER_HUMIDITY = 31
# Per-zone register 0 holds the operation mode; bits 6-7 are the sleep level.
ZONE_REGISTER_MODE = 0
ZONE_SLEEP_BIT_OFFSET = 6
# Per-zone registers 14-19 hold the zone name (12 ASCII characters).
ZONE_REGISTER_NAME = 14
ZONE_REGISTER_NAME_COUNT = 6


def _decode_name(registers):
    """Decode the 12-character zone name packed in 6 modbus registers."""
    chars = []
    for reg in registers:
        chars.append((reg >> 8) & 0xFF)
        chars.append(reg & 0xFF)
    name = bytes(c for c in chars if c).decode("ascii", errors="ignore").strip()
    return name or None


class AirzoneInnobusCoordinator(DataUpdateCoordinator):
    """Refresh the whole Innobus machine in a single modbus pass."""

    def __init__(self, hass: HomeAssistant, machine):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.machine = machine

    async def _async_update_data(self):
        """Fetch the machine state and the extra registers in one go."""
        return await self.hass.async_add_executor_job(self._refresh)

    def _refresh(self):
        """Blocking refresh executed in the executor (single modbus pass)."""
        try:
            # Refreshes the machine state and, in turn, every zone state.
            self.machine._retrieve_machine_state()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Error communicating with Airzone: {err}") from err

        data = {"min_temp": None, "max_temp": None, "zones": {}}

        # Global set-point min/max limits (system registers 25 and 26).
        try:
            regs = self.machine.read_registers(SYSTEM_REGISTER_MIN_SETPOINT, 2)
            data["min_temp"] = regs[0] / 10
            data["max_temp"] = regs[1] / 10
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not read min/max system registers (25/26): %s", err)

        for zone in self.machine.zones:
            zone_data = {
                "humidity": None,
                "low_battery": None,
                "sleep": None,
                "name": None,
            }
            try:
                humidity = self.machine.read_registers(
                    zone.base_zone + ZONE_REGISTER_HUMIDITY, 1
                )[0]
                zone_data["humidity"] = humidity if 0 <= humidity <= 100 else None
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read humidity register (31): %s", err)
            try:
                register = self.machine.read_registers(
                    zone.base_zone + ZONE_REGISTER_ERRORS, 1
                )[0]
                zone_data["low_battery"] = bool(register & (1 << ZONE_LOW_BATTERY_BIT))
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read zone errors register (13): %s", err)
            # Sleep level: bits 6-7 of the zone mode register (already fetched
            # in the zone state by the machine refresh).
            try:
                mode_register = zone.zone_state[ZONE_REGISTER_MODE]
                zone_data["sleep"] = (mode_register >> ZONE_SLEEP_BIT_OFFSET) & 0b11
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read sleep bits (register 0): %s", err)
            try:
                name_regs = self.machine.read_registers(
                    zone.base_zone + ZONE_REGISTER_NAME, ZONE_REGISTER_NAME_COUNT
                )
                zone_data["name"] = _decode_name(name_regs)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read zone name registers (14-19): %s", err)
            data["zones"][zone.unique_id] = zone_data

        return data
