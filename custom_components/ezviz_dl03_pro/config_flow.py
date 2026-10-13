"""Config flow for the Ezviz DL03 Pro lock."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from pyezvizapi import EzvizClient
from pyezvizapi.exceptions import (
    EzvizAuthVerificationCode,
    HTTPError,
    InvalidURL,
    PyEzvizError,
)
import requests
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_POLL_INTERVAL,
    CONF_REGION,
    CONF_RELOCK_SECONDS,
    CONF_REMOTE_CONTROL,
    CONF_SERIAL,
    CONF_USE_PUSH,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_REGION,
    DEFAULT_RELOCK_SECONDS,
    DEFAULT_REMOTE_CONTROL,
    DEFAULT_USE_PUSH,
    DOMAIN,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)

CONF_MFA_CODE = "mfa_code"

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
REGION_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=REGIONS, custom_value=True, mode=SelectSelectorMode.DROPDOWN
    )
)


class NeedsMfa(Exception):
    """The account requires an SMS/e-mail verification code."""


class DeviceNotFound(Exception):
    """The serial number is not in the account."""


def _login(
    client: EzvizClient, serial: str | None, mfa_code: int | None = None
) -> None:
    """Log in (blocking) and check that the lock is in the account."""
    try:
        client.login(sms_code=mfa_code)
    except EzvizAuthVerificationCode as err:
        raise NeedsMfa from err
    if serial is not None and serial not in client.get_device_infos():
        raise DeviceNotFound


class EzvizDL03ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict[str, Any] = {}
        self._client: EzvizClient | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return EzvizDL03OptionsFlow()

    async def _async_try_login(self, mfa_code: int | None = None) -> str | None:
        """Log in with self._data. Returns an error key or None on success."""
        if self._client is None:
            self._client = EzvizClient(
                self._data[CONF_USERNAME],
                self._data[CONF_PASSWORD],
                self._data.get(CONF_REGION, DEFAULT_REGION),
            )
        try:
            await self.hass.async_add_executor_job(
                _login, self._client, self._data[CONF_SERIAL], mfa_code
            )
        except NeedsMfa:
            return "mfa_required"
        except DeviceNotFound:
            return "device_not_found"
        except (InvalidURL, HTTPError, requests.RequestException, OSError):
            return "cannot_connect"
        except PyEzvizError as err:
            _LOGGER.debug("Ezviz login failed: %s", err)
            return "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected error during Ezviz login")
            return "unknown"
        finally:
            await self.hass.async_add_executor_job(self._client.close_session)
        return None

    async def _async_finish(self) -> ConfigFlowResult:
        if self.source == "reauth":
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data=self._data
            )
        return self.async_create_entry(
            title=f"Zamek {self._data[CONF_SERIAL]}", data=self._data
        )

    async def _async_handle_login(
        self, step_id: str, schema: vol.Schema
    ) -> ConfigFlowResult:
        error = await self._async_try_login()
        if error is None:
            return await self._async_finish()
        if error == "mfa_required":
            return await self.async_step_mfa()
        return self.async_show_form(
            step_id=step_id, data_schema=schema, errors={"base": error}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for account details and the lock serial number."""
        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                vol.Required(CONF_SERIAL): str,
                vol.Required(CONF_REGION, default=DEFAULT_REGION): REGION_SELECTOR,
            }
        )
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        user_input[CONF_SERIAL] = user_input[CONF_SERIAL].strip().upper()
        await self.async_set_unique_id(user_input[CONF_SERIAL])
        self._abort_if_unique_id_configured()
        self._data = dict(user_input)
        self._client = None
        return await self._async_handle_login(
            "user", self.add_suggested_values_to_schema(schema, user_input)
        )

    async def async_step_mfa(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the verification code Ezviz sent."""
        schema = vol.Schema({vol.Required(CONF_MFA_CODE): str})
        errors: dict[str, str] = {}
        if user_input is not None:
            code = user_input[CONF_MFA_CODE].strip()
            if not code.isdigit():
                errors["base"] = "invalid_mfa"
            else:
                error = await self._async_try_login(int(code))
                if error is None:
                    return await self._async_finish()
                errors["base"] = (
                    "invalid_mfa"
                    if error in ("mfa_required", "invalid_auth")
                    else error
                )
        return self.async_show_form(step_id="mfa", data_schema=schema, errors=errors)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication after the login stopped working."""
        self._data = dict(entry_data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the password again."""
        schema = vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=schema,
                description_placeholders={"username": self._data[CONF_USERNAME]},
            )
        self._data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
        self._client = None
        return await self._async_handle_login("reauth_confirm", schema)


class EzvizDL03OptionsFlow(OptionsFlow):
    """Integration options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options form."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USE_PUSH, default=DEFAULT_USE_PUSH
                ): BooleanSelector(),
                vol.Required(
                    CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=2,
                        max=60,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_RELOCK_SECONDS, default=DEFAULT_RELOCK_SECONDS
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=600,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_REMOTE_CONTROL, default=DEFAULT_REMOTE_CONTROL
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, self.config_entry.options
            ),
        )
