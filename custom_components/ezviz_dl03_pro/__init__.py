import asyncio
from datetime import timedelta
import logging
import time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    client = EzvizClient(entry.data["username"], entry.data["password"], entry.data.get("region", "eu"))
    serial_target = entry.data["serial_number"].strip()

    async def async_update_data():
        """Standardowe pobieranie danych - rygiel tu ignorujemy."""
        def fetch():
            try:
                client.login()
            except:
                pass
            return client.get_device_infos()
        
        return await hass.async_add_executor_job(fetch)

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(seconds=20),
    )

    coordinator.doorbell_ringing = False
    coordinator.last_event = "System gotowy"
    coordinator.last_event_id = ""
    coordinator.lock_state = 0 
    coordinator.unlock_time = 0 # Śledzi czas otwarcia

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        while True:
            try:
                def get_alarms():
                    return client.get_alarminfo(serial_target)
                
                response = await hass.async_add_executor_job(get_alarms)
                alarms = response.get("alarms", [])
                
                if alarms and isinstance(alarms, list) and len(alarms) > 0:
                    latest = alarms[0]
                    alarm_id = latest.get("alarmId")
                    msg_text = latest.get("alarmMessage", "")
                    
                    if alarm_id != coordinator.last_event_id:
                        coordinator.last_event_id = alarm_id
                        coordinator.last_event = msg_text
                        low_msg = msg_text.lower()
                        
                        # Otwieramy zamek i zapisujemy czas
                        if "unlock" in low_msg:
                            coordinator.lock_state = 1
                            coordinator.unlock_time = time.time()
                        elif "lock" in low_msg:
                            # Na wypadek, gdyby kiedyś zaktualizowali firmware
                            coordinator.lock_state = 0
                        
                        if "rings" in low_msg or "bell" in low_msg or "calling" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(7)
                            coordinator.doorbell_ringing = False
                        else:
                            coordinator.async_set_updated_data(coordinator.data)
                
                # --- MAGIA Z WERSJI 2.9.0 ---
                # Jeśli zamek jest w systemie OTWARTY i minęło 25 sekund od otwarcia:
                if coordinator.lock_state == 1 and (time.time() - coordinator.unlock_time) > 25:
                    coordinator.lock_state = 0 # Automatyczny powrót na Zamknięty
                    coordinator.async_set_updated_data(coordinator.data)
                    
            except Exception as err:
                _LOGGER.error("Błąd Listenera: %s", err)
            
            await asyncio.sleep(2)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-pro-turbo")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
