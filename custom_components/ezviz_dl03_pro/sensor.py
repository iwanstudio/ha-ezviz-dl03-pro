from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data.get("serial_number")
    async_add_entities([
        EzvizBatterySensor(coordinator, serial),
        EzvizEventSensor(coordinator, serial),
        EzvizWifiSignalSensor(coordinator, serial),
        EzvizWifiSSIDSensor(coordinator, serial),
        EzvizIPSensor(coordinator, serial),
        EzvizErrorSensor(coordinator, serial)
    ])

class EzvizBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Zamek DL03 Pro ({serial})")

class EzvizBatterySensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Bateria"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_batt"

    @property
    def native_value(self):
        d = self.coordinator.data.get(self.serial, {}).get("STATUS", {}).get("optionals", {}).get("multiPower", [])
        return d[0].get("Remaining") if d else None

class EzvizEventSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Ostatnie Zdarzenie"
        self._attr_icon = "mdi:history"
        self._attr_unique_id = f"{serial}_event"

    @property
    def native_value(self):
        return self.coordinator.last_event

class EzvizWifiSignalSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Sygnał Wi-Fi"
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{serial}_wifi_signal"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.serial, {}).get("WIFI", {}).get("signal")

class EzvizWifiSSIDSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Sieć Wi-Fi"
        self._attr_icon = "mdi:wifi-settings"
        self._attr_unique_id = f"{serial}_wifi_ssid"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.serial, {}).get("WIFI", {}).get("ssid")

class EzvizIPSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Adres IP"
        self._attr_icon = "mdi:ip-network"
        self._attr_unique_id = f"{serial}_ip"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.serial, {}).get("WIFI", {}).get("address")

class EzvizErrorSensor(EzvizBaseSensor):
    def __init__(self, coordinator, serial):
        super().__init__(coordinator, serial)
        self._attr_name = "Błędne próby"
        self._attr_icon = "mdi:lock-alert"
        self._attr_unique_id = f"{serial}_err"

    @property
    def native_value(self):
        feat = self.coordinator.data.get(self.serial, {}).get("FEATURE_INFO", {}).get("0", {})
        return feat.get("DoorLock", {}).get("DoorLockMgr", {}).get("TryErrLock", {}).get("errCount", 0)
