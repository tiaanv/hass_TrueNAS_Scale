"""Config flow for TrueNAS Scale 26 integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TrueNASAuthError, TrueNASConnectionError, TrueNASScaleClient
from .const import (
    CONF_API_KEY,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_USERNAME,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


class TrueNASScaleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TrueNAS Scale 26."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Handle the initial user step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            api_key = user_input[CONF_API_KEY]
            username = user_input.get(CONF_USERNAME, DEFAULT_USERNAME)
            port = user_input[CONF_PORT]
            use_ssl = user_input[CONF_SSL]
            verify_ssl = user_input[CONF_VERIFY_SSL]

            session = async_get_clientsession(self.hass)
            client = TrueNASScaleClient(
                host=host,
                api_key=api_key,
                username=username,
                port=port,
                use_ssl=use_ssl,
                verify_ssl=verify_ssl,
                session=session,
            )

            try:
                await client.connect()
                sys_info = await client.async_get_system_info()

                title = sys_info.get("hostname", host) if isinstance(sys_info, dict) else host
                unique_id = sys_info.get("system_serial") if isinstance(sys_info, dict) and sys_info.get("system_serial") else host

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"TrueNAS ({title})",
                    data=user_input,
                )
            except TrueNASAuthError:
                errors["base"] = "invalid_auth"
            except TrueNASConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception in config flow: %s", err)
                errors["base"] = "unknown"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
