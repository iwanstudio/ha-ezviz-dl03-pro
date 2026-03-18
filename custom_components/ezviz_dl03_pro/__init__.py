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
        update_interval=timedelta(minutes=5),
    )

    await coordinator.async_config_entry_first_refresh()
    coordinator.last_event = "Brak nowych zdarzeń"
    coordinator.doorbell_ringing = False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        while True:
            try:
                # Korzystamy z TESTU 2, który u Ciebie zadziałał!
                def get_alarms():
                    return client.get_alarminfo(serial_target)
                
                response = await hass.async_add_executor_job(get_alarms)
                alarms = response.get("alarms", [])
                
                if alarms and isinstance(alarms, list) and len(alarms) > 0:
                    latest = alarms[0]
                    # Tekst z logu debugowania: "Someone rings the bell"
                    msg_text = latest.get("alarmMessage", "")
                    
                    if msg_text and msg_text != coordinator.last_event:
                        _LOGGER.info(f"Wykryto zdarzenie Ezviz: {msg_text}")
                        coordinator.last_event = msg_text
                        
                        low_msg = msg_text.lower()
                        
                        # 1. LOGIKA ZAMKA
                        if "unlock" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                        elif "locked" in low_msg or "closed" in low_msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        # 2. LOGIKA DZWONKA (Dokładnie pod Twój komunikat)
                        if "rings" in low_msg or "bell" in low_msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8) # Dzwonek "dzwoni" w HA przez 8 sekund
                            coordinator.doorbell_ringing = False
                        
                        coordinator.async_set_updated_data(coordinator.data)
                
            except Exception as err:
                _LOGGER.error("Błąd podczas odczytu alarmów: %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-alarm-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
