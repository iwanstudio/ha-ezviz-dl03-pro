from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBinarySensor(coordinator, serial, "dlLock", "Zamek", BinarySensorDeviceClass.LOCK),
        EzvizBinarySensor(coordinator, serial, "dlDoor", "Drzwi", BinarySensorDeviceClass.DOOR)
    ])

class EzvizBinarySensor(BinarySensorEntity):
    def __init__(self, coordinator, serial, key, name, device_class):
        self.coordinator = coordinator
        self.serial = serial
        self.key = key
        self._attr_name = f"Ezviz {name}"
        self._attr_device_class = device_class

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        # Logika: 1 = ON (Unlocked/Open), 0 = OFF (Locked/Closed)
        return data.get(self.key) == 1
