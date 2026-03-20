import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Obsługa obu wariantów klucza loginu
    username = entry.data.get("username") or entry.data.get("email")
    password = entry.data.get("password")
    serial = entry.data.get("serial_number")

    client = EzvizClient(username, password, "eu")
    try:
        await hass.async_add_executor_job(client.login)
    except Exception as e:
        _LOGGER.error(f"Błąd logowania: {e}")
        return False

    coordinator = EzvizDataUpdateCoordinator(hass, client, serial)
    
    # Pierwsze pobranie danych
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Rejestracja trzech platform: sensor, binary_sensor i switch
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch"])
    
    return True

class EzvizDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, serial):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30)
        )
        self.ezviz_client = client
        self.serial = serial
        self.last_event = "Brak danych"
        self.doorbell_ringing = False

    async def _async_update_data(self):
        try:
            data = await self.hass.async_add_executor_job(self.ezviz_client.get_device_infos)
            msgs = await self.hass.async_add_executor_job(
                self.ezviz_client.get_device_messages_list, self.serial, 1, 10
            )
            if msgs and isinstance(msgs, list) and len(msgs) > 0:
                last_msg = msgs[0]
                msg_type = last_msg.get("alarmType", 0)
                msg_text = last_msg.get("alarmMessage", "")
                self.doorbell_ringing = (msg_type == 10000 or "doorbell" in msg_text.lower())
                
                if "unlock" in msg_text.lower():
                    if "martyna" in msg_text.lower(): self.last_event = "Martyna"
                    elif "piotrek" in msg_text.lower(): self.last_event = "Piotrek"
                    else: self.last_event = msg_text
                else:
                    self.last_event = msg_text
            return data
        except Exception as e:
            _LOGGER.error(f"Update error: {e}")
            return self.data
