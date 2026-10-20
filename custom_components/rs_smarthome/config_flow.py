"""Config flow for RS SmartHome."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import RSAuthError, RSError, RSSmartHomeApi
from .const import DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str})


class RSConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, user_input: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any] | None]:
        api = RSSmartHomeApi(async_create_clientsession(self.hass), user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
        try:
            return {}, await api.login()
        except RSAuthError:
            return {"base": "invalid_auth"}, None
        except RSError:
            return {"base": "cannot_connect"}, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, user = await self._validate(user_input)
            if user:
                await self.async_set_unique_id(str(user["AccountID"]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_USERNAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, user = await self._validate(user_input)
            if user:
                return self.async_update_reload_and_abort(self._get_reauth_entry(), data=user_input)
        return self.async_show_form(step_id="reauth_confirm", data_schema=SCHEMA, errors=errors)
