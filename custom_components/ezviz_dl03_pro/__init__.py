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
            return client.get_device_infos()
        return await hass.async_add_executor_job(fetch)

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5), # Zmieniono na 5 sekund
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.last_event_id = ""
    coordinator.last_event = "Brak nowych zdarzeń"
    coordinator.doorbell_ringing = False
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
                        _LOGGER.info(f"Nowe zdarzenie (ID: {alarm_id}): {msg_text}")
                        coordinator.last_event_id = alarm_id
                        coordinator.last_event = msg_text
                        
                        low_msg = msg_text.lower()
                        
                        # Aktualizacja stanów na podstawie tekstu alarmu
                        if "unlock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                        elif "locked" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        if "door opened" in low_msg or "is open" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 1
                        elif "door closed" in low_msg or "is closed" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 0
                        
                        if "rings" in low_msg or "bell" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8)
                            coordinator.doorbell_ringing = False
                        
                        # Natychmiastowe odświeżenie po wykryciu alarmu
                        await coordinator.async_request_refresh()
                
            except Exception as err:
                _LOGGER.error("Błąd nasłuchu zdarzeń: %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-realtime")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
