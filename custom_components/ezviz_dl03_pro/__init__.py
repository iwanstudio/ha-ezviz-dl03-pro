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
    
    # Przechowujemy czas ostatniego alarmu, żeby poller go nie nadpisał
    coordinator_extra = {
        "last_alarm_time": 0,
        "lock_hold": False
    }

    async def async_update_data():
        def fetch():
            client.login()
            return client.get_device_infos()
        
        new_data = await hass.async_add_executor_job(fetch)
        
        # Jeśli niedawno (ostatnie 20 sek) był alarm rygla, nie pozwól pollerowi go zmienić
        if coordinator.doorbell_ringing or coordinator_extra["lock_hold"]:
             _LOGGER.debug("Poller pomija aktualizację rygla/drzwi ze względu na aktywny alarm.")
             if serial_target in coordinator.data and serial_target in new_data:
                 new_data[serial_target]["STATUS"]["optionals"]["dlLock"] = coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"]
                 new_data[serial_target]["STATUS"]["optionals"]["dlDoor"] = coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"]
        
        return new_data

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.last_event_id = ""
    coordinator.last_event = "Czekam na ruch..."
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
                        _LOGGER.info(f"NOWE ZDARZENIE: {msg_text}")
                        coordinator.last_event_id = alarm_id
                        coordinator.last_event = msg_text
                        low_msg = msg_text.lower()
                        
                        # Blokujemy nadpisywanie przez poller na czas aktualizacji chmury
                        coordinator_extra["lock_hold"] = True
                        
                        # RYGIEL
                        if "unlocked" in low_msg or "unlock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                        elif "locked" in low_msg or "lock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        # DRZWI
                        if "door opened" in low_msg or "is open" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 1
                        elif "door closed" in low_msg or "is closed" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 0
                        
                        # DZWONEK
                        if "rings" in low_msg or "bell" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8)
                            coordinator.doorbell_ringing = False
                        
                        # Odświeżamy sensory w HA
                        coordinator.async_set_updated_data(coordinator.data)
                        
                        # Po 20 sekundach pozwalamy pollerowi znowu czytać z chmury (chmura powinna być już gotowa)
                        await asyncio.sleep(20)
                        coordinator_extra["lock_hold"] = False
                
            except Exception as err:
                _LOGGER.error("Błąd listenera: %s", err)
            
            await asyncio.sleep(3) # Szybszy nasłuch zdarzeń

    entry.async_create_background_task(hass, fast_listener(), "ezviz-realtime")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
