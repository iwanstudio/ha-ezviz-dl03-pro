import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezviz import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    client = EzvizClient(entry.data["username"], entry.data["password"], entry.data.get("region", "eu"))
    serial_target = entry.data["serial_number"].strip() # Czyścimy spacje
    
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
    coordinator.last_event = "Czekam na ruch..."
    coordinator.doorbell_ringing = False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        while True:
            try:
                def get_all_alarms():
                    # Pobieramy ostatnie 20 alarmów dla pewności
                    return client.get_alarm_list()
                
                response = await hass.async_add_executor_job(get_all_alarms)
                
                if response and "alarms" in response:
                    # Sprawdzamy tylko najświeższy alarm
                    alarm = response["alarms"][0]
                    
                    # Logujemy wszystko dla Twojej wiedzy - sprawdź to w logach HA!
                    _LOGGER.debug(f"Ezviz surowy alarm: {alarm}")

                    msg_full = alarm.get("alarmName", "")
                    msg = msg_full.lower()
                    alarm_serial = alarm.get("deviceSerial", "")

                    # Kluczowy moment: Sprawdzamy czy to nasz zamek
                    if alarm_serial == serial_target and msg_full != coordinator.last_event:
                        coordinator.last_event = msg_full
                        _LOGGER.info(f"WYKRYTO ZDARZENIE: {msg_full}")

                        # 1. LOGIKA ZAMKA (Unlocked / Indoor unlock)
                        if "unlocked" in msg or "otwarto" in msg or "unlock" in msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                        
                        # 2. LOGIKA ZAMYKANIA
                        elif "locked" in msg or "closed" in msg or "zamknięto" in msg:
                            coordinator.data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                        
                        # 3. LOGIKA DZWONKA (Someone rings the bell)
                        if "rings" in msg or "bell" in msg or "dzwon" in msg:
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8) # Dzwonek "świeci" 8 sekund
                            coordinator.doorbell_ringing = False
                        
                        coordinator.async_set_updated_data(coordinator.data)
                
            except Exception as err:
                _LOGGER.error("Błąd w odczycie alarmów: %s", err)
            
            await asyncio.sleep(5) # Co 5 sekund odpytujemy chmurę

    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
