import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_SERIAL, CONF_REGION, DEFAULT_REGION

class EzvizConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Tutaj można by dodać testowe logowanie, ale na start wystarczy zapis
            return self.async_create_entry(title=f"Zamek {user_input[CONF_SERIAL]}", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Required(CONF_SERIAL): str,
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): str,
            }),
            errors=errors,
        )
