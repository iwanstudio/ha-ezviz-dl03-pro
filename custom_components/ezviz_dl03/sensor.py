from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
        EzvizEventSensor(coordinator, serial) # NOWOŚĆ
    ])

class EzvizBatterySensor(CoordinatorEntity, SensorEntity):
    # ... (zachowaj kod baterii z poprzedniej wersji) ...

class EzvizEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor wyświetlający ostatni komunikat z zamka."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Ostatnie Zdarzenie"
        self._attr_icon = "mdi:history"
        self._attr_unique_id = f"{serial}_last_event"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
        )

    @property
    def native_value(self):
        return self.coordinator.last_event
