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
    
    # Przechowujemy czasy ostatnich zdarzeń, żeby uniknąć nadpisania przez chmurę
    last_updates = {
        "lock_event_time": 0,
        "door_event_time": 0
    }

    async def async_update_data():
        def fetch():
            client.login()
            return client.get_device_infos()
        
        new_data = await hass.async_add_executor_job(fetch)
        current_time = time.time()
        
        # Jeśli w ciągu ostatnich 20s był alarm rygla, nie bierz stanu z chmury (bo chmura ma laga)
        if current_time - last_updates["lock_event_time"] < 20:
            if serial_target in coordinator.data and serial_target in new_data:
                new_data[serial_target]["STATUS"]["optionals"]["dlLock"] = coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"]

        # Jeśli w ciągu ostatnich 20s był alarm drzwi, nie bierz stanu z chmury
        if current_time - last_updates["door_event_time"] < 20:
            if serial_target in coordinator.data and serial_target in new_data:
                new_data[serial_target]["STATUS"]["optionals"]["dlDoor"] = coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"]
        
        return new_data

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(seconds=10), # Poller co 10s
    )

    coordinator.doorbell_ringing = False
    coordinator.last_event = "Uruchomiono system"
    coordinator.last_event_id = ""

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
                        _LOGGER.info(f"ALARM: {msg_text}")
                        coordinator.last_event_id = alarm_id
                        coordinator.last_event = msg_text # To powinno od razu zmienić sensor zdarzeń
                        low_msg = msg_text.lower()
                        
                        # LOGIKA RYGLA
                        if "unlock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                            last_updates["lock_event_time"] = time.time()
                        elif "locked" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                            last_updates["lock_event_time"] = time.time()
                        
                        # LOGIKA DRZWI (DODANE WIĘCEJ FRAZ)
                        if any(x in low_msg for x in ["door opened", "is open", "door sensor", "opened"]):
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 1
                            last_updates["door_event_time"] = time.time()
                        elif any(x in low_msg for x in ["door closed", "is closed", "closed"]):
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 0
                            last_updates["door_event_time"] = time.time()
                        
                        # DZWONEK
                        if "rings" in low_msg or "bell" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8)
                            coordinator.doorbell_ringing = False
                        
                        # WYPYCHAMY ZMIANY DO SENSORÓW
                        coordinator.async_set_updated_data(coordinator.data)
                
            except Exception as err:
                _LOGGER.error("Błąd Listenera: %s", err)
            
            await asyncio.sleep(4)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-pro-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
