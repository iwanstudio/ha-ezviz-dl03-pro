"""Tests for setup, events and unload."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from pyezvizapi.exceptions import EzvizAuthVerificationCode, HTTPError, PyEzvizError
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.ezviz_dl03_pro.const import (
    BUS_EVENT,
    CONF_RELOCK_SECONDS,
    CONF_REMOTE_CONTROL,
    CONF_USE_PUSH,
    DOMAIN,
)

from .conftest import SERIAL, alarm


def _eid(hass: HomeAssistant, platform: str, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{SERIAL}_{key}"
    )
    assert entity_id, f"{platform} {key} not registered"
    return entity_id


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _poll(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh_alarms()
    await hass.async_block_till_done()


async def test_setup_keeps_unique_ids_and_sets_entry_id(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Old unique ids survive (automations keep working) and the entry gets a unique id."""
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.unique_id == SERIAL

    for platform, key in (
        ("binary_sensor", "lock_status"),
        ("binary_sensor", "door_status"),
        ("binary_sensor", "bell_status"),
        ("sensor", "battery"),
        ("sensor", "event"),
        ("sensor", "wifi_signal"),
        ("sensor", "wifi_ssid"),
        ("sensor", "ip_address"),
        ("sensor", "error_count"),
        ("event", "doorbell_event"),
        ("event", "activity_event"),
    ):
        _eid(hass, platform, key)

    assert hass.states.get(_eid(hass, "sensor", "battery")).state == "27"
    assert hass.states.get(_eid(hass, "binary_sensor", "door_status")).state == "off"
    # No lock entity unless remote control is enabled
    assert (
        er.async_get(hass).async_get_entity_id("lock", DOMAIN, f"{SERIAL}_lock") is None
    )


async def test_restart_does_not_replay_last_event(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """The newest historic event is shown but triggers nothing (the 3.x restart bug)."""
    events = async_capture_events(hass, BUS_EVENT)
    await _setup(hass, config_entry)

    assert hass.states.get(_eid(hass, "binary_sensor", "lock_status")).state == "off"
    last = hass.states.get(_eid(hass, "sensor", "event"))
    assert last.state == "Martyna unlocked the door with fingerprint"
    assert last.attributes["user"] == "Martyna"
    assert last.attributes["method"] == "fingerprint"
    assert events == []


async def test_new_events_all_processed_in_order(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Two events between polls are both handled, oldest first."""
    events = async_capture_events(hass, BUS_EVENT)
    await _setup(hass, config_entry)

    mock_client.get_alarminfo.return_value = {
        "alarms": [
            alarm("n2", "Jan unlocked the door with password", 2000),
            alarm("n1", "Someone rings the doorbell", 1000),
            alarm("old-2", "Martyna unlocked the door with fingerprint", 500),
        ]
    }
    await _poll(hass, config_entry)

    assert [e.data["kind"] for e in events] == ["doorbell", "unlocked"]
    assert events[1].data["user"] == "Jan"
    assert hass.states.get(_eid(hass, "binary_sensor", "lock_status")).state == "on"
    assert hass.states.get(_eid(hass, "binary_sensor", "bell_status")).state == "on"

    doorbell = hass.states.get(_eid(hass, "event", "doorbell_event"))
    assert doorbell.attributes["event_type"] == "ring"
    activity = hass.states.get(_eid(hass, "event", "activity_event"))
    assert activity.attributes["event_type"] == "unlocked"
    assert activity.attributes["user"] == "Jan"

    # Same list again: nothing new
    await _poll(hass, config_entry)
    assert len(events) == 2


async def test_doorbell_and_relock_timers(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Doorbell resets after 7 s, lock is assumed locked after the relock time."""
    await _setup(hass, config_entry)
    mock_client.get_alarminfo.return_value = {
        "alarms": [
            alarm("n2", "Jan unlocked the door with card", 2000),
            alarm("n1", "Visitor rings the doorbell", 1000),
        ]
    }
    await _poll(hass, config_entry)
    lock_id = _eid(hass, "binary_sensor", "lock_status")
    bell_id = _eid(hass, "binary_sensor", "bell_status")
    assert hass.states.get(lock_id).state == "on"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=8))
    await hass.async_block_till_done()
    assert hass.states.get(bell_id).state == "off"
    assert hass.states.get(lock_id).state == "on"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=26))
    await hass.async_block_till_done()
    assert hass.states.get(lock_id).state == "off"


async def test_relock_disabled(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """relock_seconds = 0 keeps the unlocked state until a lock event."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_USE_PUSH: False, CONF_RELOCK_SECONDS: 0}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_client.get_alarminfo.return_value = {
        "alarms": [alarm("n1", "Jan unlocked the door with card")]
    }
    await _poll(hass, config_entry)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()
    lock_id = _eid(hass, "binary_sensor", "lock_status")
    assert hass.states.get(lock_id).state == "on"

    mock_client.get_alarminfo.return_value = {
        "alarms": [
            alarm("n2", "Door locked"),
            alarm("n1", "Jan unlocked the door with card"),
        ]
    }
    await _poll(hass, config_entry)
    assert hass.states.get(lock_id).state == "off"


async def test_transient_failures_keep_entities_available(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """A few failed status polls don't make everything unavailable (the 20 s gaps)."""
    await _setup(hass, config_entry)
    battery = _eid(hass, "sensor", "battery")
    coordinator = config_entry.runtime_data
    mock_client.get_device_infos.side_effect = HTTPError("boom")

    for _ in range(3):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(battery).state == "27"

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(battery).state == "unavailable"

    mock_client.get_device_infos.side_effect = None
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(battery).state == "27"


async def test_bad_password_starts_reauth(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Wrong password → setup error + reauth flow instead of silent failures."""
    mock_client.login.side_effect = PyEzvizError("Incorrect Password.")
    config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]


@pytest.mark.parametrize(
    "error", [HTTPError("down"), PyEzvizError("Login error: 500"), OSError("net")]
)
async def test_cloud_down_retries(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_client: MagicMock,
    error: Exception,
) -> None:
    """Cloud problems at startup → retry later."""
    mock_client.login.side_effect = error
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_mfa_during_poll_starts_reauth(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """A verification-code demand during polling triggers reauth."""
    await _setup(hass, config_entry)
    mock_client.get_device_infos.side_effect = EzvizAuthVerificationCode("mfa")
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]


async def test_remote_control_lock_entity(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """With remote control enabled a lock entity unlocks through the cloud."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_USE_PUSH: False, CONF_REMOTE_CONTROL: True}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    lock_id = _eid(hass, "lock", "lock")
    assert hass.states.get(lock_id).state == "locked"
    await hass.services.async_call(
        "lock", "unlock", {"entity_id": lock_id}, blocking=True
    )
    assert mock_client.remote_unlock.called
    assert hass.states.get(lock_id).state == "unlocked"


async def test_push_triggers_fetch(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """An MQTT message for this lock fetches the new event right away."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_USE_PUSH: True})
    callbacks = {}

    def get_mqtt_client(on_message_callback):
        callbacks["cb"] = on_message_callback
        return MagicMock()

    mock_client.get_mqtt_client.side_effect = get_mqtt_client
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data
    assert coordinator.push_active

    events = async_capture_events(hass, BUS_EVENT)
    mock_client.get_alarminfo.return_value = {
        "alarms": [alarm("p1", "Guest rings the doorbell")]
    }
    # Message for another device is ignored
    await hass.async_add_executor_job(
        callbacks["cb"], {"ext": {"device_serial": "OTHER"}}
    )
    await hass.async_block_till_done()
    assert events == []

    await hass.async_add_executor_job(
        callbacks["cb"], {"ext": {"device_serial": SERIAL}}
    )
    await hass.async_block_till_done()
    assert [e.data["kind"] for e in events] == ["doorbell"]


async def test_push_failure_falls_back_to_polling(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """If MQTT can't start, the integration still loads and polls."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_USE_PUSH: True})
    mock_client.get_mqtt_client.side_effect = PyEzvizError("no push")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert not config_entry.runtime_data.push_active


async def test_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """The entry unloads cleanly (3.x needed an HA restart)."""
    await _setup(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED
