import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Próba pobrania loginu (obsługujemy obie nazwy klucza: username lub email)
    username = entry.data.get("username") or entry.data.get("email")
    password = entry.data.get("password")
    serial = entry.data.get("serial_number")

    if not username or not password or not serial:
        _LOGGER.error("Brak wymaganych danych konfiguracyjnych (login/hasło/serial)")
        return False

    # Inicjalizacja klienta Ezviz
    client = EzvizClient(username, password, "eu")
    try:
        await hass.async_add_executor_job(client.login)
    except Exception as e:
        _LOGGER.error(f"Błąd logowania do Ezviz dla użytkownika {username}: {e}")
        return False

    # Tworzymy koordynator
    coordinator = EzvizDataUpdateCoordinator(hass, client, serial)

    # WYMUSZAMY pierwsze pobranie danych przed startem sensorów
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.warning(f"Pierwsze odświeżenie danych nie powiodło się, ale kontynuujemy: {e}")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Rejestrujemy platformy
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch"])
    
    return True

class EzvizDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, serial):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.ezviz_client = client
        self.serial = serial
        self.last_event = "Brak danych"
        self.doorbell_ringing = False

    async def _async_update_data(self):
        try:
            # 1. Pobieramy pełne dane diagnostyczne
            data = await self.hass.async_add_executor_job(self.ezviz_client.get_device_infos)
            
            # 2. Pobieramy listę zdarzeń (Fast Listener)
            msgs = await self.hass.async_add_executor_job(
                self.ezviz_client.get_device_messages_list, self.serial, 1, 10
            )

            if msgs and isinstance(msgs, list) and len(msgs) > 0:
                last_msg = msgs[0]
                msg_type = last_msg.get("alarmType", 0)
                msg_text = last_msg.get("alarmMessage", "")

                # Obsługa dzwonka
                if msg_type == 10000 or "doorbell" in msg_text.lower():
                    self.doorbell_ringing = True
                else:
                    self.doorbell_ringing = False

                # Rozpoznawanie osób
                if "unlock" in msg_text.lower():
                    if "martyna" in msg_text.lower():
                        self.last_event = "Martyna"
                    elif "piotrek" in msg_text.lower():
                        self.last_event = "Piotrek"
                    else:
                        self.last_event = msg_text
                else:
                    self.last_event = msg_text

            return data
        except Exception as e:
            _LOGGER.error(f"Błąd aktualizacji danych Ezviz: {e}")
            return self.data
