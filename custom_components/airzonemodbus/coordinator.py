"""DataUpdateCoordinator for the Airzone Innobus (modbus) system."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    ZONE_REGISTER_ERRORS,
    ZONE_REGISTER_HUMIDITY,
    ZONE_REGISTER_MODE,
    ZONE_REGISTER_SETTINGS,
    ZONE_REGISTER_STATE,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

# System registers holding the global set-point min/max limits.
SYSTEM_REGISTER_MIN_SETPOINT = 25
SYSTEM_REGISTER_MAX_SETPOINT = 26
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

        # The underlying library swallows modbus/socket errors and returns None
        # instead of raising. Treat a missing machine state as a lost connection
        # so every entity is marked unavailable.
        if self.machine.machine_state is None:
            raise UpdateFailed("No response from Airzone (connection lost)")

        data = {"min_temp": None, "max_temp": None, "zones": {}}

        # Global set-point min/max limits (system registers 25 and 26).
        try:
            regs = self.machine.read_registers(SYSTEM_REGISTER_MIN_SETPOINT, 2)
            data["min_temp"] = regs[0] / 10
            data["max_temp"] = regs[1] / 10
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not read min/max system registers (25/26): %s", err)

        for zone in self.machine.zones:
            # Raw registers used by the bit-based binary sensors and selects.
            # Registers 0 (mode), 4 (settings) and 9 (state) are already in the
            # zone state fetched above; 13 (errors) and 31 (humidity) must be
            # read separately.
            registers = {}
            try:
                registers[ZONE_REGISTER_MODE] = zone.zone_state[ZONE_REGISTER_MODE]
                registers[ZONE_REGISTER_SETTINGS] = zone.zone_state[ZONE_REGISTER_SETTINGS]
                registers[ZONE_REGISTER_STATE] = zone.zone_state[ZONE_REGISTER_STATE]
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read zone state registers: %s", err)
            for addr in (ZONE_REGISTER_ERRORS, ZONE_REGISTER_HUMIDITY):
                try:
                    registers[addr] = self.machine.read_registers(
                        zone.base_zone + addr, 1
                    )[0]
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Could not read zone register %s: %s", addr, err)

            humidity = registers.get(ZONE_REGISTER_HUMIDITY)
            zone_data = {
                "registers": registers,
                "humidity": humidity if humidity is not None and 0 <= humidity <= 100 else None,
                "name": None,
            }
            try:
                name_regs = self.machine.read_registers(
                    zone.base_zone + ZONE_REGISTER_NAME, ZONE_REGISTER_NAME_COUNT
                )
                zone_data["name"] = _decode_name(name_regs)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not read zone name registers (14-19): %s", err)
            data["zones"][zone.unique_id] = zone_data

        return data
