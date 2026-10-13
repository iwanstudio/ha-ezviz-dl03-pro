"""Fixtures for Ezviz DL03 Pro tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ezviz_dl03_pro.const import (
    CONF_REGION,
    CONF_SERIAL,
    CONF_USE_PUSH,
    DOMAIN,
)

SERIAL = "BF3639401"

DEVICE = {
    SERIAL: {
        "STATUS": {"optionals": {"dlDoor": 0, "multiPower": [{"Remaining": 27}]}},
        "WIFI": {"signal": 94, "ssid": "Tenda_O3", "address": "192.168.3.125"},
        "FEATURE_INFO": {
            "0": {"DoorLock": {"DoorLockMgr": {"TryErrLock": {"errCount": 0}}}}
        },
    }
}


def alarm(alarm_id: str, message: str, ts: int | None = None) -> dict[str, Any]:
    """Build an alarm list entry."""
    data: dict[str, Any] = {"alarmId": alarm_id, "alarmMessage": message}
    if ts is not None:
        data["alarmStartTime"] = ts
    return data


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A config entry like the ones created by 3.x (no unique id)."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Zamek {SERIAL}",
        data={
            "username": "user@example.com",
            "password": "secret",
            CONF_SERIAL: SERIAL,
            CONF_REGION: "eu",
        },
        options={CONF_USE_PUSH: False},
    )


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Mock EzvizClient everywhere."""
    client = MagicMock()
    client.get_device_infos.return_value = DEVICE
    client.get_alarminfo.return_value = {
        "alarms": [alarm("old-2", "Martyna unlocked the door with fingerprint")]
    }
    with (
        patch("custom_components.ezviz_dl03_pro.EzvizClient", return_value=client),
        patch(
            "custom_components.ezviz_dl03_pro.config_flow.EzvizClient",
            return_value=client,
        ),
    ):
        yield client
