"""Binary sensors for the Ezviz DL03 Pro lock."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EzvizDL03ConfigEntry
from .entity import EzvizDL03Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EzvizDL03ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EzvizLockBinarySensor(coordinator, "lock_status"),
            EzvizDoorBinarySensor(coordinator, "door_status"),
            EzvizBellBinarySensor(coordinator, "bell_status"),
        ]
    )


class EzvizLockBinarySensor(EzvizDL03Entity, BinarySensorEntity):
    """On = unlocked. Derived from lock events (the API status is unreliable)."""

    _attr_device_class = BinarySensorDeviceClass.LOCK
    _attr_translation_key = "lock_status"

    @property
    def is_on(self) -> bool:
        """Return True when unlocked."""
        return self.coordinator.unlocked


class EzvizDoorBinarySensor(EzvizDL03Entity, BinarySensorEntity):
    """Door contact (on = open)."""

    _attr_device_class = BinarySensorDeviceClass.DOOR
    _attr_translation_key = "door"

    @property
    def is_on(self) -> bool | None:
        """Return True when the door is open."""
        value = self.optionals.get("dlDoor")
        return None if value is None else value == 1


class EzvizBellBinarySensor(EzvizDL03Entity, BinarySensorEntity):
    """On for a few seconds after the doorbell is pressed."""

    _attr_device_class = BinarySensorDeviceClass.SOUND
    _attr_translation_key = "doorbell"

    @property
    def is_on(self) -> bool:
        """Return True while ringing."""
        return self.coordinator.doorbell_ringing
