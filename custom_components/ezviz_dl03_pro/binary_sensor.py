from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizLockBinarySensor(coordinator, serial),
        EzvizDoorBinarySensor(coordinator, serial),
        EzvizBellBinarySensor(coordinator, serial),
        EzvizPrivacyBinarySensor(coordinator, serial)
    ])

class EzvizBaseBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro"
        )

class EzvizLockBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Zamek"
        self._attr_device_class = BinarySensorDeviceClass.LOCK
        self._attr_unique_id = f"{serial}_lock_status"

    @property
    def is_on(self):
        # DL03 Pro raportuje 0 jako OTWARTY (Unlocked)
        data = self.coordinator.data.get(self.serial, {})
        val = data.get("STATUS", {}).get("optionals", {}).get("dlLock")
        return val == 0

class EzvizDoorBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Drzwi"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{serial}_door_status"

    @property
    def is_on(self):
        # DL03 Pro raportuje 0 jako OTWARTE
        data = self.coordinator.data.get(self.serial, {})
        val = data.get("STATUS", {}).get("optionals", {}).get("dlDoor")
        return val == 0

class EzvizBellBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_bell_status"

    @property
    def is_on(self):
        return getattr(self.coordinator, "doorbell_ringing", False)

class EzvizPrivacyBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Tryb Prywatny"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id = f"{serial}_privacy_mode"

    @property
    def is_on(self):
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        mgr = feat.get("DoorLock", {}).get("DoorLockMgr", {})
        status_field = mgr.get("PrivacyModeStatus", {}).get("status")
        enabled_field = mgr.get("PrivacyMode", {}).get("enabled")
        return (status_field is True) or (enabled_field is True)
