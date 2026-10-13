"""Parsing of Ezviz lock alarm entries into lock events."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from .const import KIND_DOORBELL, KIND_LOCKED, KIND_OTHER, KIND_UNLOCKED

_DOORBELL_RE = re.compile(
    r"\bring(s|ing)?\b|\bdoor ?bell\b|\bcalling\b|\bdzwon", re.IGNORECASE
)
_UNLOCK_RE = re.compile(r"\bunlock(s|ed|ing)?\b|\bodblok", re.IGNORECASE)
_LOCK_RE = re.compile(r"\block(s|ed)?\b|\bzablok|\bzamkni", re.IGNORECASE)
# e.g. "Martyna unlocked the door with fingerprint"
_WHO_HOW_RE = re.compile(
    r"^(?P<user>.+?)\s+unlocked\s+the\s+door(?:\s+(?:with|by|via|using)\s+(?P<method>.+?))?\.?$",
    re.IGNORECASE,
)
_NOT_A_USER = {"door", "the door", "lock", "the lock", "someone"}


def classify(message: str) -> str:
    """Return the kind of event described by an Ezviz alarm message."""
    if _DOORBELL_RE.search(message):
        return KIND_DOORBELL
    if _UNLOCK_RE.search(message):
        return KIND_UNLOCKED
    if _LOCK_RE.search(message):
        return KIND_LOCKED
    return KIND_OTHER


@dataclass(frozen=True)
class LockEvent:
    """A single event reported by the lock."""

    alarm_id: str
    message: str
    kind: str
    user: str | None = None
    method: str | None = None
    alarm_type: Any = None
    time: str | None = None

    @classmethod
    def from_alarm(cls, alarm: dict[str, Any]) -> LockEvent:
        """Build an event from an entry of the alarm info API."""
        message = str(alarm.get("alarmMessage") or "").strip()
        user = method = None
        if match := _WHO_HOW_RE.match(message):
            user = match.group("user").strip()
            method = (match.group("method") or "").strip() or None
            if user.lower() in _NOT_A_USER:
                user = None
        raw_time = alarm.get("alarmStartTimeStr") or alarm.get("alarmStartTime")
        return cls(
            alarm_id=str(alarm.get("alarmId") or ""),
            message=message,
            kind=classify(message),
            user=user,
            method=method,
            alarm_type=alarm.get("alarmType"),
            time=str(raw_time) if raw_time is not None else None,
        )

    def as_dict(self) -> dict[str, Any]:
        """Return the event as a plain dict."""
        return asdict(self)


def sort_key(alarm: dict[str, Any]) -> tuple[float, str]:
    """Chronological sort key; the API does not return alarms newest-first.

    Uses the numeric start time when present, then the "YYYY-MM-DD HH:MM:SS"
    string (sorts correctly as text). Unknown times sort as equal.
    """
    try:
        numeric = float(alarm.get("alarmStartTime") or 0)
    except (TypeError, ValueError):
        numeric = 0.0
    return numeric, str(alarm.get("alarmStartTimeStr") or "")
