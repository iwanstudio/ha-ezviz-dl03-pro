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

class EzvizBaseBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

class EzvizLockBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Zamek"
        self._attr_device_class = BinarySensorDeviceClass.LOCK
        self._attr_unique_id = f"{serial}_lock_status"

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.serial, {})
        # 1 = Unlocked (On), 0 = Locked (Off)
        return data.get("STATUS", {}).get("optionals", {}).get("dlLock") == 1

class EzvizDoorBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Drzwi"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{serial}_door_status"

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.serial, {})
        # 1 = Open (On), 0 = Closed (Off)
        return data.get("STATUS", {}).get("optionals", {}).get("dlDoor") == 1

class EzvizBellBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_bell_status"

    @property
    def is_on(self):
        return getattr(self.coordinator, "doorbell_ringing", False)
