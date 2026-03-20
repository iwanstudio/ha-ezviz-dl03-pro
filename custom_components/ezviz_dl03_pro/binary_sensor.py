from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data.get("serial_number")
    async_add_entities([
        EzvizLockBin(coordinator, serial),
        EzvizDoorBin(coordinator, serial),
        EzvizBellBin(coordinator, serial)
    ])

class EzvizBaseBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

class EzvizLockBin(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Zamek"
        self._attr_device_class = BinarySensorDeviceClass.LOCK
        self._attr_unique_id = f"{serial}_lock"

    @property
    def is_on(self):
        # 1 = Odblokowany/Otwarty (On)
        # 0 = Zablokowany (Off)
        val = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {}).get("dlLock")
        return val == 1

class EzvizDoorBin(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Drzwi"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{serial}_door"

    @property
    def is_on(self):
        # 1 = Otwarte (On)
        val = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {}).get("dlDoor")
        return val == 1

class EzvizBellBin(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_bell"

    @property
    def is_on(self):
        return self.coordinator.doorbell_ringing
