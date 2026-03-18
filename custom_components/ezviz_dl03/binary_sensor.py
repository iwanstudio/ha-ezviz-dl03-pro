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
        EzvizDoorbellSensor(coordinator, serial)
    ])

class EzvizBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor dla rygla i skrzydła drzwi."""
    def __init__(self, coordinator, serial, key, name, device_class):
        super().__init__(coordinator)
        self.serial = serial
        self.key = key
        self._attr_name = f"Ezviz {name}"
        self._attr_device_class = device_class
        self._attr_unique_id = f"{serial}_{key}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def is_on(self):
        """Zwraca stan z danych koordynatora."""
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        # 1 = Odblokowane/Otwarte (ON), 0 = Zablokowane/Zamknięte (OFF)
        return data.get(self.key) == 1

class EzvizDoorbellSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor dzwonka wykrywający naciśnięcie przycisku."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Dzwonek"
        self._attr_device_class = BinarySensorDeviceClass.SOUND
        self._attr_unique_id = f"{serial}_doorbell"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def is_on(self):
        """Pobiera stan dzwonka ustawiony przez fast_listener w __init__.py"""
        return getattr(self.coordinator, 'doorbell_ringing', False)
