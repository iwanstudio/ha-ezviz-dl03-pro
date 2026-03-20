from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    async_add_entities([EzvizPrivacySwitch(coordinator, serial)])

class EzvizPrivacySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Przełącznik Trybu Prywatnego"
        self._attr_icon = "mdi:shield-lock"
        self._attr_unique_id = f"{serial}_privacy_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})"
        )

    @property
    def is_on(self):
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        mgr = feat.get("DoorLock", {}).get("DoorLockMgr", {})
        return mgr.get("PrivacyModeStatus", {}).get("status") is True or mgr.get("PrivacyMode", {}).get("enabled") is True

    async def async_turn_on(self, **kwargs):
        # Typ 30 = Privacy Mode w Ezviz DL03
        await self.hass.async_add_executor_job(
            self.coordinator.ezviz_client.switch_device_status, self.serial, 30, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.ezviz_client.switch_device_status, self.serial, 30, False
        )
        await self.coordinator.async_request_refresh()
