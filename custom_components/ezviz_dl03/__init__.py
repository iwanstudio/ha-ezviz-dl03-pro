import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    client = EzvizClient(entry.data["username"], entry.data["password"], entry.data.get("region", "eu"))
    
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
    coordinator.last_event = "Brak zdarzeń"
    coordinator.doorbell_ringing = False # Stan dzwonka

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        serial = entry.data["serial_number"]
        while True:
            try:
                def get_alarms():
                    return client.get_alarm_list(serial, 1, 10)
                
                alarms = await hass.async_add_executor_job(get_alarms)
                
                if alarms and "alarms" in alarms and len(alarms["alarms"]) > 0:
                    latest_alarm = alarms["alarms"][0]
                    msg = latest_alarm.get("alarmName", "").lower()
                    
                    if msg != coordinator.last_event.lower():
                        coordinator.last_event = latest_alarm.get("alarmName", "")
                        _LOGGER.debug(f"Nowe zdarzenie: {msg}")
                        
                        # LOGIKA ZAMKA
                        if "unlocked" in msg:
                            coordinator.data[serial]["STATUS"]["optionals"]["dlLock"] = 1
                        elif "locked" in msg or "closed" in msg:
                            coordinator.data[serial]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        # LOGIKA DZWONKA (szukamy frazy 'ringing' lub 'dzwonek' / 'dzwoni')
                        if "ringing" in msg or "dzwon" in msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            # Dzwonek "dzwoni" przez 10 sekund, potem gasimy stan
                            await asyncio.sleep(10)
                            coordinator.doorbell_ringing = False
                        
                        coordinator.async_set_updated_data(coordinator.data)
                
            except Exception as err:
                _LOGGER.error("Błąd nasłuchu: %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
