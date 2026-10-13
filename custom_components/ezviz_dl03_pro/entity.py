"""Base entity for the Ezviz DL03 Pro lock."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import EzvizDL03Coordinator


class EzvizDL03Entity(CoordinatorEntity[EzvizDL03Coordinator]):
    """Common entity for the lock device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EzvizDL03Coordinator, key: str) -> None:
        """Initialize; `key` is the unique id suffix (kept stable since 2.x)."""
        super().__init__(coordinator)
        serial = coordinator.serial
        self._attr_unique_id = f"{serial}_{key}"
        device = coordinator.device_data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Zamek DL03 Pro ({serial})",
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=serial,
            sw_version=device.get("version"),
        )

    @property
    def device_data(self) -> dict[str, Any]:
        """Status payload of the lock."""
        return self.coordinator.device_data

    @property
    def optionals(self) -> dict[str, Any]:
        """The STATUS.optionals section of the payload."""
        status = self.device_data.get("STATUS") or {}
        return status.get("optionals") or {}
