"""Tests for alarm message parsing."""

from __future__ import annotations

import pytest

from custom_components.ezviz_dl03_pro.events import LockEvent, classify


@pytest.mark.parametrize(
    ("message", "kind"),
    [
        ("Martyna unlocked the door with fingerprint", "unlocked"),
        ("Someone rings the doorbell", "doorbell"),
        ("Visitor is calling", "doorbell"),
        ("Door locked", "locked"),
        ("Low battery", "other"),
        ("Tampering alarm during monitoring", "other"),  # "ring" inside words
        ("", "other"),
    ],
)
def test_classify(message: str, kind: str) -> None:
    """Messages map to the right kind."""
    assert classify(message) == kind


def test_who_and_how() -> None:
    """User and method are extracted from unlock messages."""
    event = LockEvent.from_alarm(
        {
            "alarmId": 7,
            "alarmMessage": "Martyna unlocked the door with fingerprint",
            "alarmType": 10023,
            "alarmStartTimeStr": "2026-10-13 14:35:31",
        }
    )
    assert event.alarm_id == "7"
    assert event.user == "Martyna"
    assert event.method == "fingerprint"
    assert event.alarm_type == 10023
    assert event.time == "2026-10-13 14:35:31"


def test_no_user() -> None:
    """Generic messages don't invent a user."""
    event = LockEvent.from_alarm(
        {"alarmId": "1", "alarmMessage": "Door unlocked the door"}
    )
    assert event.user is None
    event = LockEvent.from_alarm(
        {"alarmId": "2", "alarmMessage": "Jan unlocked the door"}
    )
    assert (event.user, event.method) == ("Jan", None)
