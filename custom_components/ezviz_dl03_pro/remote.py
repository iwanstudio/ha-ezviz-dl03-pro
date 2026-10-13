"""Remote lock/unlock through the Ezviz IoT action API (blocking helpers).

pyezvizapi's `door_unlock()` builds the URL from `resourceId`, which for the
DL03 Pro is an internal hash, and it does not check the response code, so the
cloud silently ignored the command. Here the route uses the resource type
(`DoorLock`) and its local index, and every response is checked.
"""

from __future__ import annotations

import logging
from typing import Any

from pyezvizapi import EzvizClient
from pyezvizapi.api_endpoints import (
    API_ENDPOINT_IOT_ACTION,
    API_ENDPOINT_REMOTE_LOCK,
    API_ENDPOINT_REMOTE_UNLOCK,
)
from pyezvizapi.constants import FEATURE_CODE
from pyezvizapi.exceptions import PyEzvizError

_LOGGER = logging.getLogger(__name__)

# Door first (as in pyezvizapi), then the alternative number.
LOCK_NUMBERS = (2, 1)


class RemoteCommandFailed(PyEzvizError):
    """The cloud rejected every variant of the command."""


def lock_routes(device: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (resource, local index) candidates for the door lock."""
    routes: list[tuple[str, str]] = []
    infos = device.get("resourceInfos") or []
    if isinstance(infos, dict):
        infos = list(infos.values())
    for info in infos:
        if not isinstance(info, dict):
            continue
        category = info.get("resourceCategory") or info.get("resourceIdentifier")
        if category != "DoorLock":
            continue
        route = ("DoorLock", str(info.get("localIndex") or "0"))
        if route not in routes:
            routes.append(route)
    if not routes:
        routes.append(("DoorLock", "0"))
    return routes


def _response_code(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return None
    meta = payload.get("meta")
    if isinstance(meta, dict) and "code" in meta:
        return meta.get("code")
    return payload.get("resultCode", payload.get("status"))


def _is_ok(payload: Any) -> bool:
    code = _response_code(payload)
    return code in (200, "200", 0, "0")


def send_lock_command(
    client: EzvizClient, serial: str, device: dict[str, Any], unlock: bool
) -> dict[str, Any]:
    """Send unlock/lock, trying the known route variants. Returns what worked."""
    token = getattr(client, "_token", {}) or {}
    user = str(token.get("username") or "")
    bind_code, user_name = f"{FEATURE_CODE}{user}", user
    if unlock:
        try:
            bind_code, user_name = client.get_latest_terminal_bind(
                terminal_name="Hassio"
            )
        except Exception as err:  # noqa: BLE001 - legacy bind code still works on some
            _LOGGER.debug("No terminal bind, using legacy bind code: %s", err)

    endpoint = API_ENDPOINT_REMOTE_UNLOCK if unlock else API_ENDPOINT_REMOTE_LOCK
    failures: list[str] = []
    for resource, index in lock_routes(device):
        for lock_no in LOCK_NUMBERS:
            payload = {
                "unLockInfo": {
                    "bindCode": bind_code,
                    "lockNo": lock_no,
                    "streamToken": "",
                    "userName": user_name,
                }
            }
            path = f"{API_ENDPOINT_IOT_ACTION}{serial}/{resource}/{index}{endpoint}"
            try:
                result = client._request_json(  # noqa: SLF001
                    "PUT", path, json_body=payload, retry_401=True, max_retries=0
                )
            except PyEzvizError as err:
                failures.append(f"{resource}/{index}/lock{lock_no}: {err}")
                _LOGGER.debug("Remote %s failed via %s: %s", endpoint, path, err)
                continue
            _LOGGER.debug(
                "Remote %s via %s lockNo=%s -> %s", endpoint, path, lock_no, result
            )
            if _is_ok(result):
                return {"resource": resource, "index": index, "lock_no": lock_no}
            meta = result.get("meta") if isinstance(result, dict) else None
            message = (meta or {}).get("message") if isinstance(meta, dict) else None
            failures.append(
                f"{resource}/{index}/lock{lock_no}: code {_response_code(result)}"
                + (f" ({message})" if message else "")
            )
    raise RemoteCommandFailed("; ".join(failures) or "no route")
