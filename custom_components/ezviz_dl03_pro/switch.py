from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data.get("serial_number")
    async_add_entities([EzvizPrivacySwitch(coordinator, serial)])

class EzvizPrivacySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Przełącznik Trybu Prywatnego"
        self._attr_icon = "mdi:shield-lock"
        self._attr_unique_id = f"{serial}_priv_sw"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)}, 
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro"
        )

    @property
    def is_on(self):
        """Sprawdza stan z danych pobranych przez koordynator."""
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        mgr = feat.get("DoorLock", {}).get("DoorLockMgr", {})
        status_field = mgr.get("PrivacyModeStatus", {}).get("status")
        enabled_field = mgr.get("PrivacyMode", {}).get("enabled")
        return (status_field is True) or (enabled_field is True)

    async def async_turn_on(self, **kwargs):
        """Włącza tryb prywatny (Typ 30)."""
        # Poprawiona nazwa metody: switch_status
        await self.hass.async_add_executor_job(
            self.coordinator.ezviz_client.switch_status, self.serial, 30, 1
        )
        # Odświeżamy dane w HA, żeby przycisk od razu "zaskoczył"
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Wyłącza tryb prywatny (Typ 30)."""
        # Poprawiona nazwa metody: switch_status (używamy 0 dla OFF)
        await self.hass.async_add_executor_job(
            self.coordinator.ezviz_client.switch_status, self.serial, 30, 0
        )
        await self.coordinator.async_request_refresh()
