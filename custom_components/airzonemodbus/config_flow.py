import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_CLASS, CONF_DEVICE_ID, CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DEFAULT_DEVICE_ID, DOMAIN, MODE_NAME, SYSTEM_CLASS

_LOGGER = logging.getLogger(__name__)

AIRZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=7000): vol.Coerce(int),
        vol.Optional(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): int,
    }
)


class airzoneModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Airzone Modbus Webserver config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            from airzone import airzone_factory

            port = user_input[CONF_PORT]
            host = user_input[CONF_HOST]
            machine_id = user_input[CONF_DEVICE_ID]
            try:
                m = await self.hass.async_add_executor_job(
                    lambda: airzone_factory(host, port, machine_id, SYSTEM_CLASS)
                )
                if not m.machine_state:
                    errors["base"] = "connection"
            except Exception:  # noqa: BLE001
                errors["base"] = "connection"
            if not errors:
                # Keep the internal system class for the rest of the integration.
                user_input[CONF_DEVICE_CLASS] = SYSTEM_CLASS
                self.data = user_input

                return self.async_create_entry(
                    title=f"Airzone {MODE_NAME}", data=self.data
                )

        return self.async_show_form(
            step_id="user", data_schema=AIRZONE_SCHEMA, errors=errors
        )
