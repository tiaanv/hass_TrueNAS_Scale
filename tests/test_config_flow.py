"""Tests for TrueNAS Scale config flow."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import data_entry_flow

from custom_components.truenas_scale.config_flow import TrueNASScaleConfigFlow
from custom_components.truenas_scale.const import DOMAIN


class TestTrueNASConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test Config Flow."""

    async def test_form_user_success(self):
        flow = TrueNASScaleConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            new_callable=AsyncMock,
        ) as mock_connect:
            mock_connect.return_value = True
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "valid_key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.CREATE_ENTRY)
            self.assertEqual(result["title"], "TrueNAS SCALE (192.168.1.100)")
            self.assertEqual(result["data"]["host"], "192.168.1.100")

    async def test_form_user_invalid_auth(self):
        flow = TrueNASScaleConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        from custom_components.truenas_scale.api import TrueNASAuthError

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            side_effect=TrueNASAuthError("Invalid API key"),
        ):
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "invalid_key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.FORM)
            self.assertEqual(result["errors"]["base"], "invalid_auth")

    async def test_form_user_cannot_connect(self):
        flow = TrueNASScaleConfigFlow()
        flow.hass = MagicMock()
        flow._async_current_entries = MagicMock(return_value=[])

        from custom_components.truenas_scale.api import TrueNASConnectionError

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            side_effect=TrueNASConnectionError("Could not connect"),
        ):
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.FORM)
            self.assertEqual(result["errors"]["base"], "cannot_connect")
