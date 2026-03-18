import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    client = EzvizClient(entry.data["username"], entry.data["password"], entry.data.get("region", "eu"))
    serial_target = entry.data["serial_number"].strip()
    
    async def async_update_data():
        def fetch():
            client.login()
            # Zwraca słownik {serial: dane}
            return client.get_device_infos()
        return await hass.async_add_executor_job(fetch)

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.last_event = "Brak nowych zdarzeń"
    coordinator.doorbell_ringing = False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        while True:
            try:
                # Pobieramy listę wiadomości dla konkretnego zamka
                def get_messages():
                    return client.get_device_messages_list(serial_target)
                
                messages = await hass.async_add_executor_job(get_messages)
                
                if messages and isinstance(messages, list) and len(messages) > 0:
                    # Bierzemy najnowszą wiadomość (zazwyczaj indeks 0)
                    latest = messages[0]
                    msg_text = latest.get("msgText", "")
                    
                    if msg_text and msg_text != coordinator.last_event:
                        _LOGGER.info(f"Nowa wiadomość Ezviz: {msg_text}")
                        coordinator.last_event = msg_text
                        
                        low_msg = msg_text.lower()
                        # LOGIKA ZAMKA (Unlocked / Indoor unlock)
                        if "unlock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                        elif "locked" in low_msg or "closed" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        # LOGIKA DZWONKA (Someone rings the bell)
                        if "rings" in low_msg or "bell" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8)
                            coordinator.doorbell_ringing = False
                        
                        coordinator.async_set_updated_data(coordinator.data)
                
            except Exception as err:
                _LOGGER.error("Błąd podczas odczytu wiadomości: %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-pro-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
