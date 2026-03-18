from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
    ])

class EzvizBatterySensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"
    _attr_name = "Ezviz Bateria"

    def __init__(self, coordinator, serial):
        self.coordinator = coordinator
        self.serial = serial

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        power = data.get("multiPower", [{}])[0]
        return power.get("Remaining", 0)
