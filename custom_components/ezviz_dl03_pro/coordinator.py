"""Data coordinator for the Ezviz DL03 Pro lock."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from pyezvizapi import EzvizClient
from pyezvizapi.exceptions import (
    EzvizAuthTokenExpired,
    EzvizAuthVerificationCode,
    HTTPError,
    InvalidURL,
    PyEzvizError,
)
import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ALARM_FETCH_LIMIT,
    BUS_EVENT,
    CONF_POLL_INTERVAL,
    CONF_RELOCK_SECONDS,
    CONF_SERIAL,
    CONF_USE_PUSH,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RELOCK_SECONDS,
    DEFAULT_USE_PUSH,
    DOMAIN,
    DOORBELL_RESET_SECONDS,
    KIND_DOORBELL,
    KIND_LOCKED,
    KIND_UNLOCKED,
    MAX_TRANSIENT_FAILURES,
    PUSH_FETCH_DELAYS,
    PUSH_SAFETY_POLL,
    SEEN_IDS_MAX,
    STATUS_INTERVAL,
)
from .events import LockEvent, sort_key
from .remote import send_lock_command

_LOGGER = logging.getLogger(__name__)

TRANSIENT_ERRORS = (InvalidURL, HTTPError, requests.RequestException, OSError)

type EzvizDL03ConfigEntry = ConfigEntry[EzvizDL03Coordinator]


def is_auth_error(err: Exception) -> bool:
    """Return True if a login error means the credentials need attention."""
    if isinstance(err, EzvizAuthVerificationCode):
        return True
    text = str(err).lower()
    return any(word in text for word in ("incorrect", "user is locked", "mfa"))


class EzvizDL03Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls device status and turns lock alarms into events."""

    config_entry: EzvizDL03ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: EzvizDL03ConfigEntry, client: EzvizClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=STATUS_INTERVAL,
        )
        self.client = client
        self.serial: str = entry.data[CONF_SERIAL].strip()

        # Event-driven state
        self.unlocked = False
        self.doorbell_ringing = False
        self.last_event: LockEvent | None = None
        self.push_active = False
        self.platforms: list[str] = []
        # Last raw alarm list (trimmed), for diagnostics
        self.recent_alarms: list[dict[str, Any]] = []
        # Route that last worked for remote lock/unlock, for diagnostics
        self.last_remote: dict[str, Any] | None = None

        self._seen_ids: dict[str, None] = {}
        self._primed = False
        self._failures = 0
        self._alarm_lock = asyncio.Lock()
        self._event_callbacks: list[Callable[[LockEvent], None]] = []
        self._relock_unsub: CALLBACK_TYPE | None = None
        self._bell_unsub: CALLBACK_TYPE | None = None
        self._poll_unsub: CALLBACK_TYPE | None = None
        self._mqtt: Any = None

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------

    @property
    def relock_seconds(self) -> int:
        """Seconds after an unlock when the lock is assumed locked again."""
        return int(
            self.config_entry.options.get(CONF_RELOCK_SECONDS, DEFAULT_RELOCK_SECONDS)
        )

    @property
    def device_data(self) -> dict[str, Any]:
        """Status payload of this lock (empty when unknown)."""
        return (self.data or {}).get(self.serial) or {}

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch device status from the Ezviz cloud."""
        try:
            data = await self.hass.async_add_executor_job(self.client.get_device_infos)
        except EzvizAuthVerificationCode as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EzvizAuthTokenExpired:
            data = await self._async_relogin_and_fetch()
        except (PyEzvizError, *TRANSIENT_ERRORS) as err:
            return self._transient_failure(err)

        self._failures = 0
        if self.serial not in data:
            _LOGGER.warning(
                "Lock %s not found in the Ezviz account (devices: %s)",
                self.serial,
                ", ".join(data) or "none",
            )
        return data

    async def _async_relogin_and_fetch(self) -> dict[str, Any]:
        try:
            await self.hass.async_add_executor_job(self.client.login)
            return await self.hass.async_add_executor_job(self.client.get_device_infos)
        except PyEzvizError as err:
            if is_auth_error(err):
                raise ConfigEntryAuthFailed(str(err)) from err
            return self._transient_failure(err)
        except TRANSIENT_ERRORS as err:
            return self._transient_failure(err)

    def _transient_failure(self, err: Exception) -> dict[str, Any]:
        """Keep the last data for a few failed polls instead of going unavailable."""
        self._failures += 1
        if self.data is not None and self._failures <= MAX_TRANSIENT_FAILURES:
            _LOGGER.debug(
                "Status update failed (%s/%s), keeping last data: %s",
                self._failures,
                MAX_TRANSIENT_FAILURES,
                err,
            )
            return self.data
        raise UpdateFailed(f"Error communicating with Ezviz: {err}") from err

    # ------------------------------------------------------------------
    # Events (alarm list + MQTT push)
    # ------------------------------------------------------------------

    async def async_start_events(self) -> None:
        """Prime the event history, start push and the event poll timer."""
        await self.async_refresh_alarms()
        if self.config_entry.options.get(CONF_USE_PUSH, DEFAULT_USE_PUSH):
            await self._async_start_push()
        interval = (
            PUSH_SAFETY_POLL
            if self.push_active
            else timedelta(
                seconds=self.config_entry.options.get(
                    CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                )
            )
        )
        _LOGGER.debug(
            "Event source: %s, polling every %s",
            "MQTT push" if self.push_active else "polling",
            interval,
        )
        self._poll_unsub = async_track_time_interval(
            self.hass,
            self._async_poll_alarms,
            interval,
            name=f"{DOMAIN} event poll",
            cancel_on_shutdown=True,
        )

    async def _async_poll_alarms(self, _now: Any = None) -> None:
        await self.async_refresh_alarms()

    async def async_refresh_alarms(self) -> bool:
        """Fetch the latest alarms and process new ones. Returns True if any were new."""
        if self._alarm_lock.locked():
            return False
        async with self._alarm_lock:
            try:
                response = await self.hass.async_add_executor_job(
                    self.client.get_alarminfo, self.serial, ALARM_FETCH_LIMIT
                )
            except (PyEzvizError, *TRANSIENT_ERRORS) as err:
                _LOGGER.debug("Could not fetch lock events: %s", err)
                return False
        alarms = response.get("alarms") or []
        return self.handle_alarms([a for a in alarms if isinstance(a, dict)])

    @callback
    def handle_alarms(self, alarms: list[dict[str, Any]]) -> bool:
        """Process an alarm list (any order). Returns True if any were new."""
        with_id = [a for a in alarms if a.get("alarmId")]
        self.recent_alarms = [
            {
                key: a.get(key)
                for key in (
                    "alarmId",
                    "alarmType",
                    "alarmStartTime",
                    "alarmStartTimeStr",
                    "alarmMessage",
                )
            }
            for a in with_id
        ]

        if not self._primed:
            # First fetch after start: remember history, trigger nothing.
            self._primed = True
            for alarm in with_id:
                self._remember(str(alarm["alarmId"]))
            if with_id:
                self.last_event = LockEvent.from_alarm(max(with_id, key=sort_key))
                self.async_update_listeners()
            return False

        new = [a for a in with_id if str(a["alarmId"]) not in self._seen_ids]
        if not new:
            return False
        # Oldest first by time; with no timestamps assume the API's newest-first
        # order (stable sort keeps it).
        new.reverse()
        new.sort(key=sort_key)
        for alarm in new:
            self._remember(str(alarm["alarmId"]))
            self._process(LockEvent.from_alarm(alarm))
        self.async_update_listeners()
        return True

    def _remember(self, alarm_id: str) -> None:
        self._seen_ids[alarm_id] = None
        while len(self._seen_ids) > SEEN_IDS_MAX:
            del self._seen_ids[next(iter(self._seen_ids))]

    @callback
    def _process(self, event: LockEvent) -> None:
        _LOGGER.debug("New lock event: %s", event)
        self.last_event = event
        if event.kind == KIND_DOORBELL:
            self.doorbell_ringing = True
            if self._bell_unsub:
                self._bell_unsub()
            self._bell_unsub = async_call_later(
                self.hass, DOORBELL_RESET_SECONDS, self._reset_doorbell
            )
        elif event.kind == KIND_UNLOCKED:
            self.set_unlocked(True)
        elif event.kind == KIND_LOCKED:
            self.set_unlocked(False)

        self.hass.bus.async_fire(
            BUS_EVENT, {"serial_number": self.serial, **event.as_dict()}
        )
        for event_callback in list(self._event_callbacks):
            event_callback(event)

    @callback
    def set_unlocked(self, unlocked: bool) -> None:
        """Set the lock state; schedules the assumed auto-relock."""
        self.unlocked = unlocked
        if self._relock_unsub:
            self._relock_unsub()
            self._relock_unsub = None
        if unlocked and self.relock_seconds > 0:
            self._relock_unsub = async_call_later(
                self.hass, self.relock_seconds, self._auto_relock
            )

    @callback
    def _auto_relock(self, _now: Any) -> None:
        self._relock_unsub = None
        self.unlocked = False
        self.async_update_listeners()

    @callback
    def _reset_doorbell(self, _now: Any) -> None:
        self._bell_unsub = None
        self.doorbell_ringing = False
        self.async_update_listeners()

    @callback
    def async_add_event_callback(
        self, event_callback: Callable[[LockEvent], None]
    ) -> CALLBACK_TYPE:
        """Register a callback for new lock events."""
        self._event_callbacks.append(event_callback)

        @callback
        def _remove() -> None:
            self._event_callbacks.remove(event_callback)

        return _remove

    # ---- MQTT push ----------------------------------------------------

    async def _async_start_push(self) -> None:
        def _start() -> Any:
            mqtt = self.client.get_mqtt_client(
                on_message_callback=self._on_mqtt_message
            )
            mqtt.connect()
            return mqtt

        try:
            self._mqtt = await self.hass.async_add_executor_job(_start)
        except Exception as err:  # noqa: BLE001 - push is optional, fall back to polling
            _LOGGER.warning(
                "Ezviz push (MQTT) is unavailable, falling back to polling: %s", err
            )
            self.push_active = False
            return
        self.push_active = True

    def _on_mqtt_message(self, message: dict[str, Any]) -> None:
        """Handle a push message. Runs in the MQTT thread."""
        ext = message.get("ext") if isinstance(message.get("ext"), dict) else {}
        if str(ext.get("device_serial") or "").upper() != self.serial.upper():
            return
        self.hass.loop.call_soon_threadsafe(self._schedule_push_fetch)

    @callback
    def _schedule_push_fetch(self) -> None:
        self.config_entry.async_create_background_task(
            self.hass, self._async_push_fetch(), f"{DOMAIN} push fetch"
        )

    async def _async_push_fetch(self) -> None:
        """The push says something happened; fetch it (retrying while it lands)."""
        for delay in PUSH_FETCH_DELAYS:
            if delay:
                await asyncio.sleep(delay)
            if await self.async_refresh_alarms():
                return

    # ------------------------------------------------------------------
    # Remote control
    # ------------------------------------------------------------------

    async def async_remote(self, unlock: bool) -> None:
        """Unlock or lock the door through the Ezviz cloud."""

        try:
            self.last_remote = await self.hass.async_add_executor_job(
                send_lock_command, self.client, self.serial, self.device_data, unlock
            )
        except (PyEzvizError, *TRANSIENT_ERRORS) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unlock_failed" if unlock else "lock_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        _LOGGER.debug(
            "Remote %s accepted: %s", "unlock" if unlock else "lock", self.last_remote
        )
        self.set_unlocked(unlock)
        self.async_update_listeners()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def async_shutdown(self) -> None:
        """Stop timers and push."""
        for unsub in (self._poll_unsub, self._relock_unsub, self._bell_unsub):
            if unsub:
                unsub()
        self._poll_unsub = self._relock_unsub = self._bell_unsub = None
        if self._mqtt is not None:
            try:
                await self.hass.async_add_executor_job(self._mqtt.stop)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Error stopping Ezviz push: %s", err)
            self._mqtt = None
            self.push_active = False
        await super().async_shutdown()
