"""Tests for remote command error reporting."""

from __future__ import annotations

from unittest.mock import MagicMock

from pyezvizapi.exceptions import HTTPError
import requests

from custom_components.ezviz_dl03_pro.remote import _error_detail, lock_routes


def _http_error(status: int, body: dict | None, text: str = "") -> HTTPError:
    response = MagicMock()
    response.status_code = status
    response.json.side_effect = ValueError if body is None else None
    response.json.return_value = body
    response.text = text
    cause = requests.HTTPError(response=response)
    err = HTTPError()
    err.__cause__ = cause
    return err


def test_error_detail_with_ezviz_meta() -> None:
    """Code and message from the response body are surfaced."""
    err = _http_error(400, {"meta": {"code": 60020, "message": "device sleeping"}})
    assert _error_detail(err) == "HTTP 400, code 60020, device sleeping"


def test_error_detail_plain_text() -> None:
    """Non-JSON bodies are shown as text."""
    assert _error_detail(_http_error(500, None, "oops")) == "HTTP 500, oops"


def test_routes_fallback() -> None:
    """Without resource info the DoorLock/0 route is used."""
    assert lock_routes({}) == [("DoorLock", "0")]
