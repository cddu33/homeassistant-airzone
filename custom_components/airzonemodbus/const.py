DOMAIN = "airzonemodbus"
DEFAULT_DEVICE_ID = 1
# Display name of the only supported connection mode.
MODE_NAME = "Modbus Webserver"
# Internal system class understood by the python-airzone factory.
SYSTEM_CLASS = "innobus"
DEFAULT_DEVICE_CLASS = SYSTEM_CLASS
from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import Platform

PLATFORMS = [
    Platform.CLIMATE,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
]

# --- Per-zone modbus register addresses (relative to base_zone) ---
ZONE_REGISTER_MODE = 0       # operation mode (sleep bits 6-7)
ZONE_REGISTER_SETTINGS = 4   # zone settings (heating/floor/antifreeze, angles...)
ZONE_REGISTER_STATE = 9      # live state (demands, presence, window)
ZONE_REGISTER_ERRORS = 13    # zone errors (low battery bit 8)
ZONE_REGISTER_HUMIDITY = 31  # humidity 0-100
ZONE_LOW_BATTERY_BIT = 8

# Sleep levels (bits 6-7 of zone register 0): 0=Off, 1=30, 2=60, 3=90 minutes.
SLEEP_OPTIONS = ["arret", "30", "60", "90"]
SLEEP_BIT_OFFSET = 6

# Grille opening angle options (register 4, 2-bit fields).
GRILLE_ANGLE_OPTIONS = ["90", "50", "45", "40"]


### Innobus Extra Attributes
ATTR_IS_ZONE_GRID_OPENED = 'is_zone_grid_opened'
ATTR_IS_GRID_MOTOR_ACTIVE = 'is_grid_motor_active'
ATTR_IS_GRID_MOTOR_REQUESTED = 'is_grid_motor_requested'
ATTR_IS_FLOOR_ACTIVE = 'is_floor_active'
ATTR_LOCAL_MODULE_FANCOIL = 'get_local_module_fancoil'
ATTR_IS_REQUESTING_AIR = 'is_requesting_air'
ATTR_IS_OCCUPIED = 'is_occupied'
ATTR_IS_WINDOWS_OPENED = 'is_window_opened'
ATTR_FANCOIL_SPEED = 'get_fancoil_speed'
ATTR_PROPORTIONAL_APERTURE = 'get_proportional_aperture'
ATTR_TACTO_CONNECTED = 'is_tacto_connected_cz'
ATTR_IS_AUTOMATIC_MODE = 'is_automatic_mode'
ATTR_IS_TACTO_ON = 'is_tacto_on'
ATTR_DIF_CURRENT_TEMP = 'get_dif_current_temp'

AVAILABLE_ATTRIBUTES_ZONE = {
    ATTR_IS_ZONE_GRID_OPENED: 'is_zone_grid_opened',
    ATTR_IS_GRID_MOTOR_ACTIVE: 'is_grid_motor_active',
    ATTR_IS_GRID_MOTOR_REQUESTED: 'is_grid_motor_requested',
    ATTR_IS_FLOOR_ACTIVE: 'is_floor_active',
    ATTR_LOCAL_MODULE_FANCOIL: 'get_local_module_fancoil',
    ATTR_IS_REQUESTING_AIR: 'is_requesting_air',
    ATTR_IS_OCCUPIED: 'is_occupied',
    ATTR_IS_WINDOWS_OPENED: 'is_window_opened',
    ATTR_FANCOIL_SPEED: 'get_fancoil_speed',
    ATTR_PROPORTIONAL_APERTURE: 'get_proportional_aperture',
    ATTR_TACTO_CONNECTED: 'is_tacto_connected_cz',
    ATTR_IS_AUTOMATIC_MODE: 'is_automatic_mode',
    ATTR_IS_TACTO_ON: 'is_tacto_on',
    ATTR_DIF_CURRENT_TEMP: 'get_dif_current_temp'
}

ZONE_HVAC_MODES = [HVACMode.AUTO, HVACMode.HEAT_COOL,  HVACMode.OFF]
PRESET_SLEEP = 'SLEEP'
ZONE_PRESET_MODES = [PRESET_NONE, PRESET_SLEEP]
ZONE_FAN_MODES = {FAN_AUTO: 'AUTOMATIC', FAN_LOW: 'SPEED_1', FAN_MEDIUM: 'SPEED_2', FAN_HIGH: 'SPEED_3'}
ZONE_FAN_MODES_R = dict(zip(ZONE_FAN_MODES.values(),ZONE_FAN_MODES.keys()))
ZONE_SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

MACHINE_HVAC_MODES = [HVACMode.FAN_ONLY, HVACMode.HEAT,  HVACMode.COOL,  HVACMode.OFF]
PRESET_COMBINED_MODE = 'AIR&FLOOR'
PRESET_AIR_MODE = 'AIRE'
PRESET_FLOOR_MODE = 'FLOOR'
MACHINE_PRESET_MODES = [PRESET_AIR_MODE, PRESET_FLOOR_MODE, PRESET_COMBINED_MODE]
MACHINE_SUPPORT_FLAGS = ClimateEntityFeature.PRESET_MODE
