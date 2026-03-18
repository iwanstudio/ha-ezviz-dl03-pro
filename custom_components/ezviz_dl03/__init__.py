import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
# ZMIANA TUTAJ:
from pyezviz import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    # Inicjalizacja klienta z nowej biblioteki pyezviz
    client = EzvizClient(
        entry.data["username"], 
        entry.data["password"], 
        entry.data.get("region", "eu")
    )
    
    serial_target = entry.data["serial_number"]
    
    async def async_update_data():
        def fetch():
            client.login()
            return client.get_device_infos()
        return await hass.async_add_executor_job(fetch)

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.last_event = "Oczekiwanie na zdarzenia..."
    coordinator.doorbell_ringing = False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        while True:
            try:
                # Teraz 'get_alarm_list' zadziała, bo biblioteka pyezviz go posiada!
                def get_all_alarms():
                    return client.get_alarm_list()
                
                response = await hass.async_add_executor_job(get_all_alarms)
                
                if response and "alarms" in response:
                    for alarm in response["alarms"]:
                        if alarm.get("deviceSerial") == serial_target:
                            msg_full = alarm.get("alarmName", "")
                            msg = msg_full.lower()
                            
                            _LOGGER.debug(f"Pobrany alarm dla {serial_target}: {msg}")
                            
                            if msg_full != coordinator.last_event:
                                coordinator.last_event = msg_full
                                
                                # Logika zamka (unlocked/locked)
                                if "unlocked" in msg or "otwarto" in msg:
                                    coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                                elif "locked" in msg or "closed" in msg or "zamknięto" in msg:
                                    coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                                
                                # Logika dzwonka
                                if "ringing" in msg or "dzwon" in msg:
                                    coordinator.doorbell_ringing = True
                                    coordinator.async_set_updated_data(coordinator.data)
                                    await asyncio.sleep(5)
                                    coordinator.doorbell_ringing = False
                                
                                coordinator.async_set_updated_data(coordinator.data)
                                break
                
            except Exception as err:
                _LOGGER.error("Błąd w komunikacji z Ezviz (alarm list): %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
