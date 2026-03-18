from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Tu dodamy logikę pobierania danych z Twojego skryptu
    # zamienioną na asynchroniczne wywołania HA
    pass

class EzvizLockSensor(BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.LOCK
    _attr_name = "Ezviz Lock Status"
    
    @property
    def is_on(self):
        # Nasza logika: 0 = locked (off), 1 = unlocked (on)
        return self._status_from_api == 1
