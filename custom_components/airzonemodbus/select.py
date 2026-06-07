"""Select entities for the Airzone Modbus integration (2-bit zone fields)."""
from dataclasses import dataclass
import logging
from typing import List

from homeassistant import config_entries, core
from homeassistant.components.select import SelectEntity

from .const import (
    DOMAIN,
    GRILLE_ANGLE_OPTIONS,
    SLEEP_BIT_OFFSET,
    SLEEP_OPTIONS,
    ZONE_REGISTER_MODE,
    ZONE_REGISTER_SETTINGS,
)
from .entity import AirzoneZoneEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoneSelect:
    """Description of a 2-bit zone select field."""

    key: str
    name: str
    register: int
    bit_offset: int
    options: List[str]
    icon: str = None
    # Only relevant on zones driving a motorized grille (not on fancoils).
    requires_grid: bool = False


# 2-bit fields of the zone registers (Airzone Modbus map).
SELECTS = (
    ZoneSelect("sleep", "Veille", ZONE_REGISTER_MODE, SLEEP_BIT_OFFSET,
               SLEEP_OPTIONS, "mdi:power-sleep"),
    ZoneSelect("grille_heating", "Angle grille chaud", ZONE_REGISTER_SETTINGS, 5,
               GRILLE_ANGLE_OPTIONS, "mdi:angle-acute", requires_grid=True),
    ZoneSelect("grille_cooling", "Angle grille froid", ZONE_REGISTER_SETTINGS, 7,
               GRILLE_ANGLE_OPTIONS, "mdi:angle-acute", requires_grid=True),
)


def _zone_has_grille(zone):
    """Whether the zone drives a motorized grille (vs a fancoil).

    Grille angle settings only make sense on motorized-grid zones. If the
    capability can't be read, default to exposing the entity.
    """
    try:
        from airzone.innobus import LocalFancoilType

        return zone.get_local_module_fancoil() == LocalFancoilType.GRID
    except Exception:  # noqa: BLE001
        return True


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Airzone select entities from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for zone in data["machine"].zones:
        has_grille = _zone_has_grille(zone)
        for description in SELECTS:
            if description.requires_grid and not has_grille:
                continue
            entities.append(
                AirzoneZoneSelect(data["coordinator"], zone, description)
            )
    async_add_entities(entities)


class AirzoneZoneSelect(AirzoneZoneEntity, SelectEntity):
    """A 2-bit field of a zone register exposed as a select."""

    def __init__(self, coordinator, airzone_zone, description: ZoneSelect):
        """Initialize the device."""
        super().__init__(coordinator, airzone_zone)
        self._description = description
        self._attr_options = description.options
        self._attr_icon = description.icon
        self._attr_name = (
            "Airzone Zone " + str(airzone_zone._zone_id) + " " + description.name
        )
        self._attr_unique_id = f"{airzone_zone.unique_id}_{description.key}"

    @property
    def current_option(self):
        """Return the current option from the configured register field."""
        register = self._register(self._description.register)
        if register is None:
            return None
        index = (register >> self._description.bit_offset) & 0b11
        if index >= len(self._description.options):
            return None
        return self._description.options[index]

    def select_option(self, option: str) -> None:
        """Write the selected option into the 2-bit register field."""
        index = self._description.options.index(option)
        self._write_range(self._description.register, self._description.bit_offset, 2, index)
