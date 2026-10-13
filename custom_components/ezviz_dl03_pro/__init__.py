"""The Ezviz DL03 Pro lock integration."""

from __future__ import annotations

import logging

from pyezvizapi import EzvizClient
from pyezvizapi.exceptions import PyEzvizError
import requests

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import (
    CONF_REGION,
    CONF_REMOTE_CONTROL,
    CONF_SERIAL,
    DEFAULT_REGION,
    DEFAULT_REMOTE_CONTROL,
)
from .coordinator import EzvizDL03ConfigEntry, EzvizDL03Coordinator, is_auth_error

_LOGGER = logging.getLogger(__name__)

BASE_PLATFORMS = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


def _platforms(entry: EzvizDL03ConfigEntry) -> list[Platform]:
    if entry.options.get(CONF_REMOTE_CONTROL, DEFAULT_REMOTE_CONTROL):
        return [*BASE_PLATFORMS, Platform.LOCK]
    return BASE_PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: EzvizDL03ConfigEntry) -> bool:
    """Set up the lock from a config entry."""
    serial = entry.data[CONF_SERIAL].strip()
    if entry.unique_id is None:
        # Entries created before 4.0 had no unique id.
        hass.config_entries.async_update_entry(entry, unique_id=serial.upper())

    client = EzvizClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_REGION, DEFAULT_REGION),
    )
    try:
        await hass.async_add_executor_job(client.login)
    except PyEzvizError as err:
        if is_auth_error(err):
            raise ConfigEntryAuthFailed(str(err)) from err
        raise ConfigEntryNotReady(f"Ezviz login failed: {err}") from err
    except (requests.RequestException, OSError) as err:
        raise ConfigEntryNotReady(f"Cannot reach Ezviz: {err}") from err

    coordinator = EzvizDL03Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    coordinator.platforms = _platforms(entry)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, coordinator.platforms)
    await coordinator.async_start_events()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: EzvizDL03ConfigEntry
) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EzvizDL03ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, entry.runtime_data.platforms
    )
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded
