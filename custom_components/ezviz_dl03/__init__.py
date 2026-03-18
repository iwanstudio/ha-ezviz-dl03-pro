import asyncio
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyezvizapi import EzvizClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    client = EzvizClient(
        entry.data["username"], 
        entry.data["password"], 
        entry.data.get("region", "eu")
    )
    
    # Koordynator zostaje dla pełnych danych (np. bateria raz na jakiś czas)
    async def async_update_data():
        def fetch():
            client.login()
            return client.get_device_infos()
        return await hass.async_add_executor_job(fetch)

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="ezviz_dl03",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5), # Bateria nie musi być często
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # --- NOWOŚĆ: Zadanie w tle do szybkiego wykrywania zmian ---
    async def fast_listener():
        _LOGGER.info("Uruchomiono szybki nasłuch zdarzeń dla Ezviz")
        while True:
            try:
                # Sprawdzamy alarmy co 10 sekund (możesz skrócić do 5)
                # To nie drenuje baterii zamka, bo pytamy chmurę, a nie zamek bezpośrednio
                def get_alarms():
                    return client.get_alarm_list()
                
                alarms = await hass.async_add_executor_job(get_alarms)
                
                # Jeśli w alarmach jest coś nowego, wymuszamy odświeżenie statusu
                if alarms:
                    _LOGGER.debug("Wykryto zdarzenie Ezviz, odświeżam sensory...")
                    await coordinator.async_refresh()
                
            except Exception as err:
                _LOGGER.error("Błąd w szybkim nasłuchu: %s", err)
            
            await asyncio.sleep(10) # Tu sterujesz "szybkością" reakcji

    # Uruchamiamy nasłuch jako zadanie w tle
    entry.async_create_background_task(hass, fast_listener(), "ezviz-fast-listener")

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
