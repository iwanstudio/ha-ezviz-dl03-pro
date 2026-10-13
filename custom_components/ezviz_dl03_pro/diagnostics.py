"""Diagnostics for the Ezviz DL03 Pro lock."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import EzvizDL03ConfigEntry

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "address",
    "netIp",
    "wanIp",
    "localIp",
    "mac",
    "ssid",
    "deviceSerial",
    "serial_number",
    "streamToken",
    "token",
    "password",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EzvizDL03ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics (helps map event messages and status fields)."""
    coordinator = entry.runtime_data
    event = coordinator.last_event
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "push_active": coordinator.push_active,
        "unlocked": coordinator.unlocked,
        "last_event": event.as_dict() if event else None,
        "recent_alarms": coordinator.recent_alarms,
        "last_remote": coordinator.last_remote,
        "device": async_redact_data(coordinator.device_data, TO_REDACT),
    }
