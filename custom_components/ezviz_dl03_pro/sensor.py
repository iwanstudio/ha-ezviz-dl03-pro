from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
        EzvizEventSensor(coordinator, serial)
    ])

class EzvizBatterySensor(CoordinatorEntity, SensorEntity):
    """Sensor baterii."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Poziom Baterii"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_battery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        power_list = data.get("multiPower", [])
        if power_list:
            return power_list[0].get("Remaining", 0)
        return None

class EzvizEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor wyświetlający ostatni komunikat z alarmu."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Ostatnie Zdarzenie"
        self._attr_icon = "mdi:history"
        self._attr_unique_id = f"{serial}_last_event"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def native_value(self):
        return getattr(self.coordinator, 'last_event', "Brak zdarzeń")
