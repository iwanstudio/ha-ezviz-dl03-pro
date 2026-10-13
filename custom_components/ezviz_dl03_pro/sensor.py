"""Sensors for the Ezviz DL03 Pro lock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EzvizDL03ConfigEntry, EzvizDL03Coordinator
from .entity import EzvizDL03Entity


def _battery(data: dict[str, Any]) -> Any:
    power = ((data.get("STATUS") or {}).get("optionals") or {}).get("multiPower")
    if isinstance(power, list) and power and isinstance(power[0], dict):
        return power[0].get("Remaining")
    return None


def _wifi(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda data: (data.get("WIFI") or {}).get(key)


def _error_count(data: dict[str, Any]) -> Any:
    feature = (data.get("FEATURE_INFO") or {}).get("0") or {}
    return (
        feature.get("DoorLock", {})
        .get("DoorLockMgr", {})
        .get("TryErrLock", {})
        .get("errCount")
    )


@dataclass(frozen=True, kw_only=True)
class EzvizSensorDescription(SensorEntityDescription):
    """Describes a status sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[EzvizSensorDescription, ...] = (
    EzvizSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_battery,
    ),
    EzvizSensorDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_wifi("signal"),
    ),
    EzvizSensorDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_wifi("ssid"),
    ),
    EzvizSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_wifi("address"),
    ),
    EzvizSensorDescription(
        key="error_count",
        translation_key="error_count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_error_count,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EzvizDL03ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(EzvizStatusSensor(coordinator, desc) for desc in SENSORS),
            EzvizLastEventSensor(coordinator, "event"),
        ]
    )


class EzvizStatusSensor(EzvizDL03Entity, SensorEntity):
    """A value read from the device status."""

    entity_description: EzvizSensorDescription

    def __init__(
        self, coordinator: EzvizDL03Coordinator, description: EzvizSensorDescription
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the value."""
        return self.entity_description.value_fn(self.device_data)


class EzvizLastEventSensor(EzvizDL03Entity, SensorEntity):
    """Text of the latest lock event, with who/how as attributes."""

    _attr_translation_key = "last_event"

    @property
    def native_value(self) -> str | None:
        """Return the event message."""
        event = self.coordinator.last_event
        return event.message[:255] if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return event details."""
        event = self.coordinator.last_event
        if event is None:
            return None
        return {
            "type": event.kind,
            "user": event.user,
            "method": event.method,
            "time": event.time,
            "alarm_type": event.alarm_type,
        }
