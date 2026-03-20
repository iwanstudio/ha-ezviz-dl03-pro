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
    
    # Przechowujemy czasy, aby uniknąć nadpisania przez chmurę (ochrona przed lagiem)
    last_updates = {"lock_event_time": 0, "door_event_time": 0}

    def process_alarms(alarms, current_data):
        """Wspólna logika przetwarzania alarmów dla rygla, drzwi i dzwonka."""
        if not alarms or not isinstance(alarms, list):
            return
            
        # Szukamy najnowszych zdarzeń w historii 10 alarmów
        for alarm in reversed(alarms): # Od najstarszego do najnowszego
            msg_text = alarm.get("alarmMessage", "")
            low_msg = msg_text.lower()
            
            # Stan rygla
            if "unlock" in low_msg:
                current_data[serial_target]["STATUS"]["optionals"]["dlLock"] = 1
                last_updates["lock_event_time"] = time.time()
            elif "lock" in low_msg:
                current_data[serial_target]["STATUS"]["optionals"]["dlLock"] = 0
                last_updates["lock_event_time"] = time.time()
            
            # Stan drzwi
            if any(x in low_msg for x in ["door opened", "is open", "opened", "open"]):
                current_data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 1
                last_updates["door_event_time"] = time.time()
            elif any(x in low_msg for x in ["door closed", "is closed", "closed", "close"]):
                current_data[serial_target]["STATUS"]["optionals"]["dlDoor"] = 0
                last_updates["door_event_time"] = time.time()

        # Obsługa ostatniego zdarzenia dla sensora
        latest = alarms[0]
        coordinator.last_event_id = latest.get("alarmId")
        msg_text = latest.get("alarmMessage", "")
        if "unlock" in msg_text.lower():
            if "martyna" in msg_text.lower(): coordinator.last_event = "Martyna"
            elif "piotrek" in msg_text.lower(): coordinator.last_event = "Piotrek"
            else: coordinator.last_event = msg_text
        else:
            coordinator.last_event = msg_text

    async def async_update_data():
        """Standardowe odświeżanie (co 15s) - teraz z 'łatką' alarmów."""
        def fetch_all():
            client.login()
            device_info = client.get_device_infos()
            alarms_info = client.get_alarminfo(serial_target)
            return device_info, alarms_info.get("alarms", [])
        
        device_data, alarms = await hass.async_add_executor_job(fetch_all)
        
        # 'Łatamy' dane z chmury informacjami z alarmów, żeby stan nie skakał
        process_alarms(alarms, device_data)
        return device_data

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03_pro",
        update_method=async_update_data,
        update_interval=timedelta(seconds=15),
    )

    coordinator.doorbell_ringing = False
    coordinator.last_event = "Inicjalizacja..."
    coordinator.last_event_id = ""

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        """Błyskawiczny nasłuchiwacz (2s) dla dzwonka i szybkich zmian."""
        while True:
            try:
                def get_alarms():
                    return client.get_alarminfo(serial_target)
                
                response = await hass.async_add_executor_job(get_alarms)
                alarms = response.get("alarms", [])
                
                if alarms:
                    latest = alarms[0]
                    if latest.get("alarmId") != coordinator.last_event_id:
                        # Przetwarzamy alarmy i wymuszamy aktualizację encji
                        process_alarms(alarms, coordinator.data)
                        
                        # Specyficzna obsługa dzwonka
                        if any(x in latest.get("alarmMessage", "").lower() for x in ["rings", "bell", "calling"]):
                            coordinator.doorbell_ringing = True
                            coordinator.async_set_updated_data(coordinator.data)
                            await asyncio.sleep(8)
                            coordinator.doorbell_ringing = False
                        
                        coordinator.async_set_updated_data(coordinator.data)
            except Exception as err:
                _LOGGER.error("Błąd Listenera: %s", err)
            await asyncio.sleep(2)

    entry.async_create_background_task(hass, fast_listener(), "ezviz-pro-turbo")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
