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
        EzvizBinarySensor(coordinator, serial, "dlDoor", "Drzwi", BinarySensorDeviceClass.DOOR),
        EzvizDoorbellSensor(coordinator, serial) # NOWOŚĆ
    ])

class EzvizBinarySensor(CoordinatorEntity, BinarySensorEntity):
    # ... (zachowaj kod zamka i drzwi z poprzedniej wersji) ...

class EzvizDoorbellSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor dzwonka."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_doorbell"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
        )

    @property
    def is_on(self):
        return getattr(self.coordinator, 'doorbell_ringing', False)
