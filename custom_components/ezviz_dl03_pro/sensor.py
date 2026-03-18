from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data["serial_number"]
    
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
        EzvizEventSensor(coordinator, serial),
        EzvizWifiSignalSensor(coordinator, serial),
        EzvizErrorCountSensor(coordinator, serial)
    ])

class EzvizBaseSensor(CoordinatorEntity, SensorEntity):
    """Baza dla wszystkich sensorów zamka."""
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer="Ezviz",
            model="DL03 Pro"
        )

class EzvizBatterySensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Bateria"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_battery"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.serial, {})
        power = data.get("STATUS", {}).get("optionals", {}).get("multiPower", [])
        if power and len(power) > 0:
            return power[0].get("Remaining")
        return None

class EzvizEventSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Ostatnie Zdarzenie"
        self._attr_icon = "mdi:history"
        self._attr_unique_id = f"{serial}_last_event"

    @property
    def native_value(self):
        return getattr(self.coordinator, "last_event", "Brak danych")

class EzvizWifiSignalSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Sygnał Wi-Fi"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_wifi_signal"

    @property
    def native_value(self):
        # Pobieranie sygnału z sekcji WIFI (wartość 58 z Twojego testu)
        return self.coordinator.data.get(self.serial, {}).get("WIFI", {}).get("signal")

class EzvizErrorCountSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ezviz Błędne Próby"
        self._attr_icon = "mdi:alert-lock"
        self._attr_unique_id = f"{serial}_error_count"

    @property
    def native_value(self):
        # Ścieżka: FEATURE_INFO -> 0 -> DoorLock -> DoorLockMgr -> TryErrLock -> errCount
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        return feat.get("DoorLock", {}).get("DoorLockMgr", {}).get("TryErrLock", {}).get("errCount", 0)
