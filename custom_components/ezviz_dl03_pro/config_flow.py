import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_SERIAL, CONF_REGION, DEFAULT_REGION

class EzvizConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Obsługa przepływu konfiguracji dla Ezviz DL03."""
    
    VERSION = 1  # <--- TO JEST KLUCZOWE! Bez tego HA wywala błąd 500.

    async def async_step_user(self, user_input=None):
        """Obsługa pierwszego kroku logowania."""
        errors = {}
        
        if user_input is not None:
            # Tworzymy wpis w HA
            return self.async_create_entry(
                title=f"Zamek {user_input[CONF_SERIAL]}", 
                data=user_input
            )

        # Formularz wyświetlany użytkownikowi
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
