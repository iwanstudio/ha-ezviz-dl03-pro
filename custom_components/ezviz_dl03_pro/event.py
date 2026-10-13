"""Event entities for the Ezviz DL03 Pro lock (doorbell press, lock activity)."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import KIND_DOORBELL, KIND_LOCKED, KIND_OTHER, KIND_UNLOCKED
from .coordinator import EzvizDL03ConfigEntry
from .entity import EzvizDL03Entity
from .events import LockEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EzvizDL03ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up event entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EzvizDoorbellEvent(coordinator, "doorbell_event"),
            EzvizActivityEvent(coordinator, "activity_event"),
        ]
    )


class _EzvizEventBase(EzvizDL03Entity, EventEntity):
    """Fires when the coordinator reports a matching lock event."""

    _kinds: frozenset[str] = frozenset()

    async def async_added_to_hass(self) -> None:
        """Subscribe to lock events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_event_callback(self._handle_lock_event)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Status updates don't change event entities."""

    @callback
    def _handle_lock_event(self, event: LockEvent) -> None:
        if event.kind not in self._kinds:
            return
        self._trigger_event(
            self._event_type(event),
            {
                "message": event.message,
                "user": event.user,
                "method": event.method,
                "time": event.time,
            },
        )
        self.async_write_ha_state()

    def _event_type(self, event: LockEvent) -> str:
        return event.kind


class EzvizDoorbellEvent(_EzvizEventBase):
    """Doorbell press."""

    _attr_device_class = EventDeviceClass.DOORBELL
    _attr_translation_key = "doorbell_event"
    _attr_event_types = ["ring"]
    _kinds = frozenset({KIND_DOORBELL})

    def _event_type(self, event: LockEvent) -> str:
        return "ring"


class EzvizActivityEvent(_EzvizEventBase):
    """Unlock / lock / other lock activity."""

    _attr_translation_key = "activity_event"
    _attr_event_types = [KIND_UNLOCKED, KIND_LOCKED, KIND_OTHER]
    _kinds = frozenset({KIND_UNLOCKED, KIND_LOCKED, KIND_OTHER})
