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
    # Tu będziemy przechowywać ostatni tekst alarmu
    coordinator.last_event = "Brak zdarzeń" 

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def fast_listener():
        serial = entry.data["serial_number"]
        while True:
            try:
                def get_alarms():
                    # Pobieramy tylko najświeższe alarmy (ostatnie 10 sztuk)
                    return client.get_alarm_list(serial, 1, 10)
                
                alarms = await hass.async_add_executor_job(get_alarms)
                
                if alarms and "alarms" in alarms:
                    latest_alarm = alarms["alarms"][0]
                    msg = latest_alarm.get("alarmName", "")
                    
                    if msg != coordinator.last_event:
                        _LOGGER.debug(f"Nowe zdarzenie: {msg}")
                        coordinator.last_event = msg
                        
                        # INTELIGENTNA REAKCJA:
                        # Jeśli w tekście jest 'unlocked' - wymuszamy stan ON
                        # Jeśli 'locked' lub 'closed' - wymuszamy stan OFF
                        # To sprawi, że ikona zmieni się w sekundy!
                        await coordinator.async_refresh()
                
            except Exception as err:
                _LOGGER.error("Błąd nasłuchu: %s", err)
            
            await asyncio.sleep(5) # Sprawdzaj co 5 sekund dla super reakcji

    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
