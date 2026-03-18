import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
# Używamy dokładnie tego samego importu co HP7
from pyezviz.client import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    # Inicjalizacja klienta
    client = EzvizClient(
        entry.data["username"], 
        entry.data["password"], 
        entry.data.get("region", "eu")
    )
    
    serial_target = entry.data["serial_number"].strip()
    
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
                # DEBUG: Sprawdzamy czy metoda w ogóle istnieje w załadowanym obiekcie
                if not hasattr(client, 'get_alarm_list'):
                    _LOGGER.error("KRYTYCZNY BŁĄD: Załadowana biblioteka wciąż NIE POSIADA get_alarm_list! Restart HA jest niezbędny.")
                    await asyncio.sleep(60)
                    continue

                def get_all_alarms():
                    return client.get_alarm_list()
                
                response = await hass.async_add_executor_job(get_all_alarms)
                
                if response and "alarms" in response:
                    for alarm in response["alarms"]:
                        if alarm.get("deviceSerial") == serial_target:
                            msg_full = alarm.get("alarmName", "")
                            msg = msg_full.lower()
                            
                            if msg_full != coordinator.last_event:
                                coordinator.last_event = msg_full
                                _LOGGER.info(f"Nowy alarm złapany: {msg_full}")
                                
                                # Logika zamka na podstawie Twoich zdjęć:
                                if "unlocked" in msg or "unlock" in msg:
                                    coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                                elif "locked" in msg or "closed" in msg:
                                    coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                                
                                # Logika dzwonka (Someone rings the bell)
                                if "rings" in msg or "bell" in msg:
                                    coordinator.doorbell_ringing = True
                                    coordinator.async_set_updated_data(coordinator.data)
                                    await asyncio.sleep(6)
                                    coordinator.doorbell_ringing = False
                                
                                coordinator.async_set_updated_data(coordinator.data)
                                break
                
            except Exception as err:
                _LOGGER.error("Błąd podczas sprawdzania alarmów: %s", err)
            
            await asyncio.sleep(5)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
