"""Shared base entity for the Airzone Modbus zone entities."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class AirzoneZoneEntity(CoordinatorEntity):
    """Base entity attached to an Airzone zone device."""

    def __init__(self, coordinator, airzone_zone):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._airzone_zone = airzone_zone

    @property
    def _zone_data(self):
        """Coordinator data for this zone."""
        return self.coordinator.data["zones"].get(self._airzone_zone.unique_id, {})

    def _register(self, addr):
        """Return the cached value of a zone register, or None."""
        return self._zone_data.get("registers", {}).get(addr)

    @property
    def device_info(self) -> DeviceInfo:
        """Attach to the same device as the zone climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._airzone_zone.unique_id)},
            via_device=(DOMAIN, self._airzone_zone._machine.unique_id),
        )

    def _read_register(self, relative_addr):
        """Read a single zone register live from the bus (relative address)."""
        return self._airzone_zone._machine.read_registers(
            self._airzone_zone.base_zone + relative_addr, 1
        )[0]

    def _write_bit(self, relative_addr, bit, value):
        """Set or clear a single bit of a zone register (read-modify-write)."""
        current = self._read_register(relative_addr)
        if value:
            current |= 1 << bit
        else:
            current &= ~(1 << bit)
        self._airzone_zone.write_register(relative_addr, current)

    def _write_range(self, relative_addr, bit_offset, num_bits, value):
        """Write a multi-bit field of a zone register (read-modify-write)."""
        current = self._read_register(relative_addr)
        mask = ((1 << num_bits) - 1) << bit_offset
        current = (current & ~mask) | ((value << bit_offset) & mask)
        self._airzone_zone.write_register(relative_addr, current)
