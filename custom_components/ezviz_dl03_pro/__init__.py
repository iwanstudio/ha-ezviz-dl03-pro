import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
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
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True

class EzvizDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, serial):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, 
            update_interval=timedelta(seconds=5)
        )
        self.ezviz_client = client
        self.serial = serial
        self.last_event = "Brak danych"
        self.doorbell_ringing = False

    async def _async_update_data(self):
        try:
            # Pobieramy dane diagnostyczne
            data = await self.hass.async_add_executor_job(self.ezviz_client.get_device_infos)
            
            # Pobieramy 10 ostatnich komunikatów (większy bufor niż 5)
            msgs = await self.hass.async_add_executor_job(
                self.ezviz_client.get_device_messages_list, self.serial, 1, 10
            )
            
            if msgs and isinstance(msgs, list) and len(msgs) > 0:
                m = msgs[0]
                m_type = m.get("alarmType", 0)
                m_text = m.get("alarmMessage", "")
                
                # Dzwonek (typ 10000)
                self.doorbell_ringing = (m_type == 10000 or "doorbell" in m_text.lower())
                
                # Rozpoznawanie osób i otwarć
                if "unlock" in m_text.lower():
                    if "martyna" in m_text.lower(): self.last_event = "Martyna"
                    elif "piotrek" in m_text.lower(): self.last_event = "Piotrek"
                    else: self.last_event = "Otwarto"
                else:
                    self.last_event = m_text
            else:
                # Jeśli lista jest pusta, resetujemy tylko dzwonek
                self.doorbell_ringing = False

            return data
        except Exception as e:
            _LOGGER.error(f"Błąd odświeżania danych: {e}")
            return self.data
