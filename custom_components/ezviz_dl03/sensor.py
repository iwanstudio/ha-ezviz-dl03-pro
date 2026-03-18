from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
    ])

class EzvizBatterySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_name = "Ezviz Poziom Baterii"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_battery"
        
        # Identyczne DeviceInfo jak w binary_sensor sprawi, że trafią do tego samego okna
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro",
        )

    @property
    def native_value(self):
        """Zwraca poziom baterii z danych koordynatora."""
        data = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {})
        # Pobieramy Remaining z pierwszego elementu listy multiPower
        power_list = data.get("multiPower", [])
        if power_list:
            return power_list[0].get("Remaining", 0)
        return None
