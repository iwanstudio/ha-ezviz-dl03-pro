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
        # KONIEC KŁAMSTW EZVIZA: Czytamy wyłącznie naszą własną, wyliczoną zmienną z historii
        return getattr(self.coordinator, "lock_state", 0) == 1

class EzvizDoorBinarySensor(EzvizBaseBinary):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Drzwi"
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"{serial}_door_status"

    @property
    def is_on(self):
        # Drzwi działają w API poprawnie, więc czytamy z danych (1 = Otwarte)
        data = self.coordinator.data.get(self.serial, {})
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
