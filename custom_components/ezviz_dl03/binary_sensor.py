from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBinarySensor(coordinator, serial, "dlLock", "Zamek", BinarySensorDeviceClass.LOCK),
        EzvizBinarySensor(coordinator, serial, "dlDoor", "Drzwi", BinarySensorDeviceClass.DOOR)
    ])

class EzvizBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, serial, key, name, device_class):
        super().__init__(coordinator)
        self.serial = serial
        self.key = key
        self._attr_name = f"Ezviz {name}"
        self._attr_device_class = device_class
        self._attr_unique_id = f"{serial}_{key}"
        
        # To grupuje encje w jedno urządzenie w HA
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def is_on(self):
        """Zwraca True, jeśli zamek jest odblokowany lub drzwi otwarte."""
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        # 1 = ON (Open/Unlocked), 0 = OFF (Closed/Locked)
        return data.get(self.key) == 1
