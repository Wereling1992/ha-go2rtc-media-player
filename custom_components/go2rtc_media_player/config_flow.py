"""Config flow for go2rtc Media Player."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AUDIO_OPTIONS,
    CONF_AUDIO,
    CONF_STREAM,
    CONF_URL,
    DEFAULT_AUDIO,
    DEFAULT_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_go2rtc(hass: HomeAssistant, url: str) -> bool:
    """Return True if go2rtc API responds."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(f"{url.rstrip('/')}/api", timeout=5) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


class Go2rtcMediaPlayerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for go2rtc Media Player."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            stream = user_input[CONF_STREAM].strip()
            audio = user_input[CONF_AUDIO]
            url = user_input.get(CONF_URL, DEFAULT_URL).rstrip("/")

            await self.async_set_unique_id(f"{url}_{stream}")
            self._abort_if_unique_id_configured()

            if not await validate_go2rtc(self.hass, url):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_STREAM: stream,
                        CONF_AUDIO: audio,
                        CONF_URL: url,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_STREAM): str,
                    vol.Required(CONF_AUDIO, default=DEFAULT_AUDIO): vol.In(
                        AUDIO_OPTIONS
                    ),
                    vol.Optional(CONF_URL, default=DEFAULT_URL): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return Go2rtcMediaPlayerOptionsFlow()


class Go2rtcMediaPlayerOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
                title=user_input.get(CONF_NAME, self.config_entry.title),
            )
            return self.async_create_entry(title="", data={})

        data = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=data.get(CONF_NAME)): str,
                    vol.Required(CONF_STREAM, default=data.get(CONF_STREAM)): str,
                    vol.Required(
                        CONF_AUDIO, default=data.get(CONF_AUDIO, DEFAULT_AUDIO)
                    ): vol.In(AUDIO_OPTIONS),
                    vol.Optional(
                        CONF_URL, default=data.get(CONF_URL, DEFAULT_URL)
                    ): str,
                }
            ),
        )
