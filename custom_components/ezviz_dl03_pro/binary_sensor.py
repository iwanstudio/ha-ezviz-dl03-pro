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
        EzvizBellBinarySensor(coordinator, serial)
    ])

class EzvizLockBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Zamek"
        self._attr_unique_id = f"{serial}_lock_status"
        self._attr_device_class = BinarySensorDeviceClass.LOCK
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

    @property
    def is_on(self):
        # Bezpieczne pobieranie danych (zabezpieczenie przed None)
        data = self.coordinator.data.get(self.serial, {}) if self.coordinator.data else {}
        status = data.get("STATUS", {}) or {}
        opts = status.get("optionals", {}) or {}
        return opts.get("dlLock") == 1

    @property
    def icon(self):
        return "mdi:lock-open-variant" if self.is_on else "mdi:lock"

class EzvizDoorBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Drzwi"
        self._attr_unique_id = f"{serial}_door_status"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.serial, {}) if self.coordinator.data else {}
        status = data.get("STATUS", {}) or {}
        opts = status.get("optionals", {}) or {}
        return opts.get("dlDoor") == 1

    @property
    def icon(self):
        return "mdi:door-open" if self.is_on else "mdi:door-closed"

class EzvizBellBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Dzwonek"
        self._attr_unique_id = f"{serial}_bell_status"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

    @property
    def is_on(self):
        return getattr(self.coordinator, "doorbell_ringing", False)

    @property
    def icon(self):
        return "mdi:bell-ring" if self.is_on else "mdi:bell-outline"
