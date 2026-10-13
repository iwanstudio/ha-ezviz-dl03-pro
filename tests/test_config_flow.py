"""Tests for the config and options flows."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from pyezvizapi.exceptions import EzvizAuthVerificationCode, HTTPError, PyEzvizError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ezviz_dl03_pro.const import (
    CONF_POLL_INTERVAL,
    CONF_RELOCK_SECONDS,
    CONF_REMOTE_CONTROL,
    CONF_USE_PUSH,
    DOMAIN,
)

from .conftest import SERIAL

USER_INPUT = {
    "username": "user@example.com",
    "password": "secret",
    "serial_number": f" {SERIAL.lower()} ",
    "region": "eu",
}


@pytest.fixture(autouse=True)
def skip_setup() -> Generator[None]:
    """Don't set up the entry after the flow creates it."""
    with patch("custom_components.ezviz_dl03_pro.async_setup_entry", return_value=True):
        yield


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Happy path: credentials are checked, serial normalized, unique id set."""
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["serial_number"] == SERIAL
    assert result["result"].unique_id == SERIAL
    mock_client.login.assert_called_once()


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (PyEzvizError("Incorrect Password."), "invalid_auth"),
        (HTTPError("down"), "cannot_connect"),
        (RuntimeError("?"), "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, mock_client: MagicMock, error: Exception, key: str
) -> None:
    """Login errors are shown on the form, then the user can retry."""
    mock_client.login.side_effect = error
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": key}

    mock_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_device_not_found(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """A serial that isn't in the account is rejected."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "serial_number": "XX0000000"}
    )
    assert result["errors"] == {"base": "device_not_found"}


async def test_mfa_flow(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Accounts with verification codes get an extra step."""
    mock_client.login.side_effect = [
        EzvizAuthVerificationCode("mfa"),
        EzvizAuthVerificationCode("bad code"),
        None,
    ]
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["step_id"] == "mfa"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "abc"}
    )
    assert result["errors"] == {"base": "invalid_mfa"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "111111"}
    )
    assert result["errors"] == {"base": "invalid_mfa"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "123456"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    mock_client.login.assert_called_with(sms_code=123456)


async def test_duplicate_aborts(
    hass: HomeAssistant, mock_client: MagicMock, config_entry: MockConfigEntry
) -> None:
    """The same lock can't be added twice."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, unique_id=SERIAL)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant, mock_client: MagicMock, config_entry: MockConfigEntry
) -> None:
    """Reauth updates the stored password."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, unique_id=SERIAL)
    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"password": "new-secret"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data["password"] == "new-secret"


async def test_options_flow(
    hass: HomeAssistant, mock_client: MagicMock, config_entry: MockConfigEntry
) -> None:
    """Options are saved."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_USE_PUSH: False,
            CONF_POLL_INTERVAL: 3,
            CONF_RELOCK_SECONDS: 30,
            CONF_REMOTE_CONTROL: True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_RELOCK_SECONDS] == 30
    assert config_entry.options[CONF_REMOTE_CONTROL] is True
