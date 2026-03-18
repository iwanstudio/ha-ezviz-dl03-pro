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
        data = self.coordinator.data.get(self.serial, {})
        return data.get("STATUS", {}).get("optionals", {}).get("dlLock") == 1

    @property
    def icon(self):
        return "mdi:lock-open-variant" if self.is_on else "mdi:lock"

class EzvizDoorBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Drzwi"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{serial}_door_status"

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.serial, {})
        return data.get("STATUS", {}).get("optionals", {}).get("dlDoor") == 1

    @property
    def icon(self):
        return "mdi:door-open" if self.is_on else "mdi:door-closed"

class EzvizBellBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_bell_status"

    @property
    def is_on(self):
        return getattr(self.coordinator, "doorbell_ringing", False)

    @property
    def icon(self):
        return "mdi:bell-ring" if self.is_on else "mdi:bell-outline"

class EzvizPrivacyBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Tryb Prywatny"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id = f"{serial}_privacy_mode"

    @property
    def is_on(self):
        # Ścieżka: FEATURE_INFO -> 0 -> DoorLock -> DoorLockMgr -> PrivacyModeStatus -> status
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        status = feat.get("DoorLock", {}).get("DoorLockMgr", {}).get("PrivacyModeStatus", {}).get("status")
        return status is True

    @property
    def icon(self):
        return "mdi:shield-lock" if self.is_on else "mdi:shield-off-outline"
