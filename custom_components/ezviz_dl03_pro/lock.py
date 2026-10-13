"""Lock entity (remote lock/unlock), enabled in the integration options."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EzvizDL03ConfigEntry
from .entity import EzvizDL03Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EzvizDL03ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lock entity."""
    async_add_entities([EzvizDL03Lock(entry.runtime_data, "lock")])


class EzvizDL03Lock(EzvizDL03Entity, LockEntity):
    """The door lock, controlled through the Ezviz cloud."""

    _attr_name = None  # main feature of the device: named after the device

    @property
    def is_locked(self) -> bool:
        """Return True when locked (state derived from lock events)."""
        return not self.coordinator.unlocked

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the door."""
        await self.coordinator.async_remote(unlock=True)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the door."""
        await self.coordinator.async_remote(unlock=False)
